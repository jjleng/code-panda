const { createClient, defaultPlugins } = require('@hey-api/openapi-ts'); // eslint-disable-line

const services = {
  agent: `${process.env.AGENT_BASE}/openapi.json`,
  runner: `${process.env.RUNNER_BASE}/openapi.json`,
};

Object.entries(services).forEach(([serviceName, url]) => {
  createClient({
    client: '@hey-api/client-fetch',
    input: url,
    output: {
      path: `src/generated/${serviceName}`,
    },
    plugins: [...defaultPlugins, '@tanstack/react-query'],
  });
});
