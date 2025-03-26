(function () {
  const sendNavigation = () => {
    window.parent.postMessage(
      {
        type: 'navigation',
        path: window.location.pathname,
      },
      '*'
    );
  };

  // Intercept History API
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;

  history.pushState = function () {
    originalPushState.apply(this, arguments);
    sendNavigation();
  };

  history.replaceState = function () {
    originalReplaceState.apply(this, arguments);
    sendNavigation();
  };

  // Send initial navigation
  sendNavigation();

  // Listen for popstate (browser back/forward)
  window.addEventListener('popstate', sendNavigation);
})();
