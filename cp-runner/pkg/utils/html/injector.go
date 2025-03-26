package html

import (
	"bytes"
	"fmt"
	"log"
	"strings"

	"golang.org/x/net/html"
)

// ScriptConfig represents configuration for script injection
type ScriptConfig struct {
	Content     string            // The JavaScript content to inject
	Attributes  map[string]string // HTML attributes for the script tag
	InsertFirst bool              // Whether to insert at the beginning of head
}

// HTMLInjector provides utilities for injecting content into HTML documents
type HTMLInjector struct {
	scripts []ScriptConfig
}

// NewHTMLInjector creates a new HTMLInjector instance
func NewHTMLInjector() *HTMLInjector {
	return &HTMLInjector{
		scripts: make([]ScriptConfig, 0),
	}
}

// AddScript adds a script configuration to be injected
func (i *HTMLInjector) AddScript(config ScriptConfig) {
	i.scripts = append(i.scripts, config)
}

// ensureHead ensures that the document has a head element, creating it if necessary
func ensureHead(doc *html.Node) (*html.Node, error) {
	// First try to find existing head
	var head *html.Node
	var findHead func(*html.Node)
	findHead = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "head" {
			head = n
			return
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			findHead(c)
		}
	}
	findHead(doc)

	if head != nil {
		return head, nil
	}

	// If no head found, try to find html tag
	var htmlNode *html.Node
	var findHtml func(*html.Node)
	findHtml = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "html" {
			htmlNode = n
			return
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			findHtml(c)
		}
	}
	findHtml(doc)

	if htmlNode == nil {
		return nil, fmt.Errorf("no <html> tag found in document")
	}

	// Create and insert head tag
	head = &html.Node{
		Type: html.ElementNode,
		Data: "head",
	}

	if htmlNode.FirstChild != nil {
		htmlNode.InsertBefore(head, htmlNode.FirstChild)
	} else {
		htmlNode.AppendChild(head)
	}
	log.Printf("Created new <head> tag")

	return head, nil
}

// InjectIntoHTML modifies the provided HTML content by injecting configured scripts
func (i *HTMLInjector) InjectIntoHTML(content []byte) ([]byte, error) {
	doc, err := html.Parse(bytes.NewReader(content))
	if err != nil {
		return nil, fmt.Errorf("failed to parse HTML: %w", err)
	}

	head, err := ensureHead(doc)
	if err != nil {
		return nil, fmt.Errorf("failed to ensure head element: %w", err)
	}

	// Inject scripts
	for _, script := range i.scripts {
		scriptNode := &html.Node{
			Type: html.ElementNode,
			Data: "script",
		}

		// Add attributes
		for key, value := range script.Attributes {
			scriptNode.Attr = append(scriptNode.Attr, html.Attribute{
				Key: key,
				Val: value,
			})
		}

		// Add content if provided
		if script.Content != "" {
			scriptNode.AppendChild(&html.Node{
				Type: html.TextNode,
				Data: strings.TrimSpace(script.Content),
			})
		}

		// Insert at beginning or end of head
		if script.InsertFirst {
			if head.FirstChild != nil {
				head.InsertBefore(scriptNode, head.FirstChild)
			} else {
				head.AppendChild(scriptNode)
			}
			log.Printf("Injected script at the beginning of <head>")
		} else {
			head.AppendChild(scriptNode)
			log.Printf("Injected script at the end of <head>")
		}
	}

	// Render modified HTML
	var buf bytes.Buffer
	err = html.Render(&buf, doc)
	if err != nil {
		return nil, fmt.Errorf("failed to render modified HTML: %w", err)
	}

	return buf.Bytes(), nil
}
