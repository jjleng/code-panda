package runtime

import "fmt"

type PackageManager int

const (
	NPM PackageManager = iota
	YARN
	PNPM
)

func ParsePackageManager(s string) (PackageManager, error) {
	switch s {
	case "npm":
		return NPM, nil
	case "yarn":
		return YARN, nil
	case "pnpm":
		return PNPM, nil
	default:
		return PackageManager(-1), fmt.Errorf("invalid package manager: %s", s)
	}
}

func (pm PackageManager) IsValid() bool {
	switch pm {
	case NPM, YARN, PNPM:
		return true
	default:
		return false
	}
}

func (pm PackageManager) String() string {
	switch pm {
	case NPM:
		return "npm"
	case YARN:
		return "yarn"
	case PNPM:
		return "pnpm"
	default:
		return "unknown"
	}
}

func (pm PackageManager) GetInstallCmd() string {
	switch pm {
	case NPM:
		return "npm install"
	case YARN:
		return "yarn install"
	case PNPM:
		return "pnpm install"
	default:
		return ""
	}
}

func (pm PackageManager) GetDevCmd() string {
	switch pm {
	case NPM:
		return "npm run dev"
	case YARN:
		return "yarn dev"
	case PNPM:
		return "pnpm dev"
	default:
		return ""
	}
}

func (pm PackageManager) GetLintCmd() string {
	switch pm {
	case NPM:
		return "npm run lint"
	case YARN:
		return "yarn lint"
	case PNPM:
		return "pnpm lint"
	default:
		return ""
	}
}

func (pm PackageManager) GetBuildCmd() string {
	switch pm {
	case NPM:
		return "npm run build"
	case YARN:
		return "yarn build"
	case PNPM:
		return "pnpm build"
	default:
		return ""
	}
}

func (pm PackageManager) GetTypeCheckCmd() string {
	switch pm {
	case NPM:
		return "npm exec -- tsc --noEmit --incremental -p tsconfig.app.json"
	case YARN:
		return "yarn tsc --noEmit --incremental -p tsconfig.app.json"
	case PNPM:
		return "pnpm exec tsc --noEmit --incremental -p tsconfig.app.json"
	default:
		return ""
	}
}
