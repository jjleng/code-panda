import mermaid from 'mermaid';
import React, { useEffect, useRef, useState } from 'react';

interface Props {
  chart: string;
}

export const Mermaid: React.FC<Props> = ({ chart }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [id] = useState(() => `mermaid-${Math.random().toString(36).substring(2)}`);

  useEffect(() => {
    const renderChart = async () => {
      if (!ref.current) return;

      try {
        // Initialize mermaid only once
        mermaid.initialize({
          startOnLoad: false, // Changed to false to prevent auto-loading
          theme: 'default',
          securityLevel: 'loose',
        });

        // Add small delay to ensure initialization is complete
        await new Promise(resolve => setTimeout(resolve, 100));

        const { svg } = await mermaid.render(id, chart.trim());
        if (ref.current) {
          ref.current.innerHTML = svg;
          const svgElement = ref.current.querySelector('svg');
          if (svgElement) {
            svgElement.style.maxWidth = '100%';
            svgElement.style.height = 'auto';
          }
        }
      } catch (error) {
        console.log('Failed to render mermaid chart:', error);
        if (ref.current) {
          ref.current.innerHTML = `<div class="text-red-500 p-4 border border-red-300 rounded">
            Failed to render diagram. Please check the syntax.
          </div>`;
        }
      }
    };

    renderChart();
  }, [chart, id]);

  return <div className="my-4 flex w-full justify-center overflow-x-auto" ref={ref} />;
};
