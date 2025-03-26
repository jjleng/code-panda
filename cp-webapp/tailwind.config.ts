import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
  	extend: {
  		keyframes: {
  			'pulse-radius': {
  				'0%, 100%': {
  					transform: 'scale(1)'
  				},
  				'50%': {
  					transform: 'scale(1.5)'
  				}
  			},
  			'spin-slow': {
  				from: {
  					transform: 'rotate(0deg)'
  				},
  				to: {
  					transform: 'rotate(360deg)'
  				}
  			},
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'pulse-radius': 'pulse-radius 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  			'spin-slow': 'spin-slow 8s linear infinite',
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		},
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))'
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		typography: {
  			DEFAULT: {
  				css: {
  					'h1, h2, h3, h4, h5, h6': {
  						marginTop: '1rem',
  						marginBottom: '0.5rem',
  						fontWeight: '600'
  					},
  					h1: {
  						fontSize: '1.5rem',
  						lineHeight: '2rem'
  					},
  					h2: {
  						fontSize: '1.25rem',
  						lineHeight: '1.75rem'
  					},
  					h3: {
  						fontSize: '1.125rem',
  						lineHeight: '1.5rem'
  					},
  					ul: {
  						marginTop: '0.3rem',
  						marginBottom: '0.3rem',
  						paddingLeft: '1.5rem',
  						listStyleType: 'disc'
  					},
  					ol: {
  						marginTop: '0.3rem',
  						marginBottom: '0.3rem',
  						paddingLeft: '1.5rem',
  						listStyleType: 'decimal'
  					},
  					p: {
  						marginTop: '0.3rem',
  						marginBottom: '0.3rem',
  						'&:first-child, &:last-child': {
  							display: 'inline',
  							marginTop: '10px'
  						}
  					},
  					a: {
  						color: 'hsl(var(--primary))',
  						textDecoration: 'underline',
  						'&:hover': {
  							opacity: 0.8
  						}
  					},
  					pre: {
  						padding: '.5rem',
  						borderRadius: 'var(--radius)',
  						overflowX: 'auto',
  						width: '100%'
  					},
  					code: {
  						backgroundColor: 'hsl(var(--muted))',
  						padding: '0.25rem',
  						borderRadius: '0.25rem',
  						fontSize: '0.875rem',
  						margin: 0
  					}
  				}
  			}
  		}
  	}
  },
  plugins: [
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('tailwindcss-animate'),
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('@tailwindcss/typography'),
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    require('tailwind-scrollbar')({
      preferredStrategy: 'pseudoelements',
      nocompatible: true,
    }),
  ],
} satisfies Config;
