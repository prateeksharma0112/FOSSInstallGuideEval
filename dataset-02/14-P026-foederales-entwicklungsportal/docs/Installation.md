## How to build

To build the developer portal locally [yarn package manager](https://yarnpkg.com/) is recommended.

### Preconditions
To install yarn:
```sh
npm install --global yarn
```

Before proceeding, double check that yarn is installed correctly:
```sh
yarn --version
```

### Environment Variables
The application uses the following environment variables for configuration:

#### Plausible Analytics
- `NEXT_PUBLIC_PLAUSIBLE_DOMAIN`: The domain for Plausible analytics tracking (default: `docs.fitko.de`)
- `NEXT_PUBLIC_PLAUSIBLE_ANALYTICS_URL`: The URL for the Plausible analytics dashboard (default: `https://plausible.io/docs.fitko.de`)

To override these values, create a `.env.local` file in the root directory:
```bash
# .env.local
NEXT_PUBLIC_PLAUSIBLE_DOMAIN=your-domain.com
NEXT_PUBLIC_PLAUSIBLE_ANALYTICS_URL=https://plausible.io/your-domain.com
```

### Start development environment
Let's start the integrated Next.js development server:
```sh
yarn install
yarn dev
```

By default, the server runs on [http://localhost:3000](http://localhost:3000)

### Production build
Build a fully deployable export with:
```sh
yarn install
yarn export
```

The result is stored in the `build` directory.
