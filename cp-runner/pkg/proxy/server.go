package proxy

import (
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	html "github.com/jjleng/cp-runner/pkg/utils/html"
)

type ProxyServer struct {
	server    *http.Server
	appPort   int
	isLoading atomic.Bool
	cache     *staticFileCache
}

// staticFileCache provides thread-safe caching of static files
type staticFileCache struct {
	mu    sync.RWMutex
	files map[string][]byte
}

func newStaticFileCache() *staticFileCache {
	return &staticFileCache{
		files: make(map[string][]byte),
	}
}

func (c *staticFileCache) get(filename string) ([]byte, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	content, exists := c.files[filename]
	return content, exists
}

func (c *staticFileCache) set(filename string, content []byte) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.files[filename] = content
}

func NewProxyServer(port int, targetPort int) *ProxyServer {
	ps := &ProxyServer{
		appPort: targetPort,
		cache:   newStaticFileCache(),
	}
	ps.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: http.HandlerFunc(ps.proxyHandler),
	}

	// Preload static files
	ps.preloadStaticFiles()
	return ps
}

func (p *ProxyServer) preloadStaticFiles() {
	files := []string{"loading.html", "heartbeat.js", "navigation.js"}
	for _, filename := range files {
		content, err := p.readStaticFile(filename)
		if err != nil {
			log.Printf("Warning: Failed to preload %s: %v", filename, err)
			continue
		}
		p.cache.set(filename, content)
	}
}

func (p *ProxyServer) Start() error {
	return p.server.ListenAndServe()
}

func (p *ProxyServer) Stop() error {
	// Create a context with timeout for graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Attempt graceful shutdown first
	if err := p.server.Shutdown(ctx); err != nil {
		// If graceful shutdown fails, force close
		return p.server.Close()
	}
	return nil
}

func (p *ProxyServer) SetLoadingMode(loading bool) {
	p.isLoading.Store(loading)
}

// readStaticFile reads a file from the static directory with caching
func (p *ProxyServer) readStaticFile(filename string) ([]byte, error) {
	// Check cache first
	if content, exists := p.cache.get(filename); exists {
		return content, nil
	}

	// Get the directory of the currently executing binary
	exePath, err := os.Executable()
	if err != nil {
		return nil, fmt.Errorf("failed to get executable path: %v", err)
	}
	exeDir := filepath.Dir(exePath)

	// Construct the path to the static file
	staticPath := filepath.Join(exeDir, "static", filename)

	// Read the file
	content, err := os.ReadFile(staticPath)
	if err != nil {
		// Try development path if production path fails
		devPath := filepath.Join("static", filename)
		content, err = os.ReadFile(devPath)
		if err != nil {
			return nil, fmt.Errorf("failed to read static file %s: %v", filename, err)
		}
	}

	// Cache the content
	p.cache.set(filename, content)
	return content, nil
}

func (p *ProxyServer) proxyHandler(w http.ResponseWriter, r *http.Request) {
	// Set CORS headers for all responses
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Accept, Authorization, Content-Type, Upgrade, Connection")

	// Handle preflight requests
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	if p.isLoading.Load() {
		// Check if request is for HTML or a static asset
		acceptHeader := strings.ToLower(r.Header.Get("Accept"))
		path := r.URL.Path

		// Treat requests with Accept header containing "text/html" or requests with
		// no file extension or ending with "/" as requests for HTML content
		wantsHTML := strings.Contains(acceptHeader, "text/html") ||
			!strings.Contains(path[strings.LastIndex(path, "/")+1:], ".") ||
			strings.HasSuffix(path, "/")

		if wantsHTML {
			// Serve loading.html for HTML requests
			loadingHTML, err := p.readStaticFile("loading.html")
			if err != nil {
				log.Printf("Error reading loading.html: %v", err)
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
				return
			}
			w.Header().Set("Content-Type", "text/html")
			w.WriteHeader(http.StatusOK)
			w.Write(loadingHTML)
		} else {
			// For static assets, return 503 Service Unavailable with Retry-After header
			w.Header().Set("Retry-After", "2") // Suggest retry after 2 seconds
			w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate")
			http.Error(w, "Service Unavailable - Server is restarting", http.StatusServiceUnavailable)
		}
		return
	}

	if isWebSocketUpgrade(r) {
		p.handleWebSocket(w, r)
		return
	}

	p.proxyHTTPRequest(w, r)
}

func isWebSocketUpgrade(r *http.Request) bool {
	return strings.ToLower(r.Header.Get("Upgrade")) == "websocket" &&
		strings.ToLower(r.Header.Get("Connection")) == "upgrade"
}

func (p *ProxyServer) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	targetConn, err := net.Dial("tcp", fmt.Sprintf("localhost:%d", p.appPort))
	if err != nil {
		http.Error(w, "Could not connect to app server", http.StatusServiceUnavailable)
		return
	}
	defer targetConn.Close()

	err = r.Write(targetConn)
	if err != nil {
		http.Error(w, "Failed to proxy WebSocket request", http.StatusInternalServerError)
		return
	}

	hj, ok := w.(http.Hijacker)
	if !ok {
		http.Error(w, "WebSocket proxy not supported", http.StatusInternalServerError)
		return
	}
	clientConn, _, err := hj.Hijack()
	if err != nil {
		http.Error(w, "Failed to hijack connection", http.StatusInternalServerError)
		return
	}
	defer clientConn.Close()

	go func() {
		io.Copy(targetConn, clientConn)
	}()
	io.Copy(clientConn, targetConn)
}

func (p *ProxyServer) proxyHTTPRequest(w http.ResponseWriter, r *http.Request) {
	targetURL := fmt.Sprintf("http://localhost:%d%s", p.appPort, r.URL.RequestURI())

	proxyReq, err := http.NewRequest(r.Method, targetURL, r.Body)
	if err != nil {
		http.Error(w, "Failed to create proxy request", http.StatusInternalServerError)
		return
	}

	for key, values := range r.Header {
		for _, value := range values {
			proxyReq.Header.Add(key, value)
		}
	}

	client := &http.Client{}
	resp, err := client.Do(proxyReq)
	if err != nil {
		log.Printf("Failed to proxy request to app server: %v", err)
		http.Error(w, "App server unavailable", http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	// Copy headers, but skip Content-Length and cache-related headers
	for key, values := range resp.Header {
		k := strings.ToLower(key)
		if k != "content-length" &&
			k != "cache-control" &&
			k != "etag" &&
			k != "last-modified" {
			for _, value := range values {
				w.Header().Add(key, value)
			}
		}
	}

	// Add cache control headers
	w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0")
	w.Header().Set("Pragma", "no-cache")
	w.Header().Set("Expires", "0")

	// Check if response is HTML
	contentType := resp.Header.Get("Content-Type")
	isHTML := strings.Contains(strings.ToLower(contentType), "text/html")

	if isHTML {
		// Read the entire response body
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Error reading response body: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}

		log.Printf("Starting HTML injection process...")

		injector := html.NewHTMLInjector()

		// Read and inject heartbeat script
		heartbeatJS, err := p.readStaticFile("heartbeat.js")
		if err != nil {
			log.Printf("Error reading heartbeat.js: %v", err)
		} else {
			injector.AddScript(html.ScriptConfig{
				Content:     string(heartbeatJS),
				InsertFirst: true,
			})
		}

		// Read and inject navigation script
		navigationJS, err := p.readStaticFile("navigation.js")
		if err != nil {
			log.Printf("Error reading navigation.js: %v", err)
		} else {
			injector.AddScript(html.ScriptConfig{
				Content:     string(navigationJS),
				InsertFirst: true,
			})
		}

		modifiedBody, err := injector.InjectIntoHTML(body)
		if err != nil {
			log.Printf("Error injecting HTML: %v", err)
			// Fall back to sending original response
			w.WriteHeader(resp.StatusCode)
			w.Write(body)
			return
		}

		// Write the modified response
		w.WriteHeader(resp.StatusCode)
		if _, err := w.Write(modifiedBody); err != nil {
			log.Printf("Error writing modified response: %v", err)
		}
	} else {
		// For non-HTML responses, simply copy the response as-is
		w.WriteHeader(resp.StatusCode)
		if _, err := io.Copy(w, resp.Body); err != nil {
			log.Printf("Error copying response: %v", err)
		}
	}
}

func FindFreePort() (int, error) {
	addr, err := net.ResolveTCPAddr("tcp", "localhost:0")
	if err != nil {
		return 0, err
	}

	l, err := net.ListenTCP("tcp", addr)
	if err != nil {
		return 0, err
	}
	defer l.Close()
	return l.Addr().(*net.TCPAddr).Port, nil
}
