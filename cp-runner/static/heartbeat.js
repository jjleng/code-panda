(function () {
  const EVENTS = ['mousedown', 'keydown', 'scroll', 'mousemove'];

  function handleActivity(event) {
    // Send activity event to parent window
    window.parent.postMessage({ type: 'activity', event }, '*');
  }

  // Set up event listeners for user activity
  EVENTS.forEach((event) => {
    window.addEventListener(event, () => handleActivity(event));
  });
})();
