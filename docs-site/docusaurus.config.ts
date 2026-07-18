import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const GITHUB_ORG = 'Lee-Dongwook';
const GITHUB_REPO = 'E2E-Self-Heal';
const GITHUB_URL = `https://github.com/${GITHUB_ORG}/${GITHUB_REPO}`;

// Deployment URLs. Served as a GitHub Pages *project* site under /<repo>/.
const SITE_URL = `https://${GITHUB_ORG.toLowerCase()}.github.io`;
const BASE_URL = `/${GITHUB_REPO}/`;
const FULL_URL = `${SITE_URL}${BASE_URL}`; // https://lee-dongwook.github.io/E2E-Self-Heal/

// Analytics / SEO — supplied via env so IDs are never hardcoded or committed.
// Set these as CI secrets (see .github/workflows/deploy-docs.yml) or a local .env.
const GA4_ID = process.env.GA4_ID; // GA4 Measurement ID, e.g. G-XXXXXXXXXX
const GOOGLE_SITE_VERIFICATION = process.env.GOOGLE_SITE_VERIFICATION; // Search Console token

const SITE_DESCRIPTION =
  'E2E-Healer auto-repairs broken Playwright E2E tests. When a UI change breaks a ' +
  "selector, an AI agent diagnoses the failure, patches the locator, verifies it against " +
  'the live DOM, and re-runs until green — as a local CLI or a CI GitHub Action that opens a patch PR.';

const config: Config = {
  title: 'E2E-Healer',
  tagline:
    'Self-healing Playwright E2E tests — auto-patch broken selectors, or review them at the source.',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Production URL (GitHub Pages). Served under /<repo>/.
  url: SITE_URL,
  baseUrl: BASE_URL,

  // Global <head> tags: structured data for search/AI engines (GEO) and the
  // optional Search Console verification token.
  headTags: [
    {
      tagName: 'link',
      attributes: {rel: 'preconnect', href: 'https://www.googletagmanager.com'},
    },
    {
      // JSON-LD so Google and generative engines (ChatGPT/Perplexity crawlers)
      // can understand what this project is, at a glance.
      tagName: 'script',
      attributes: {type: 'application/ld+json'},
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: 'E2E-Healer',
        applicationCategory: 'DeveloperApplication',
        operatingSystem: 'Linux, macOS, Windows',
        description: SITE_DESCRIPTION,
        url: FULL_URL,
        codeRepository: GITHUB_URL,
        license: 'https://opensource.org/licenses/MIT',
        offers: {'@type': 'Offer', price: '0', priceCurrency: 'USD'},
        author: {'@type': 'Person', name: 'Lee Dongwook'},
      }),
    },
    ...(GOOGLE_SITE_VERIFICATION
      ? [
          {
            tagName: 'meta',
            attributes: {
              name: 'google-site-verification',
              content: GOOGLE_SITE_VERIFICATION,
            },
          },
        ]
      : []),
  ],

  // GitHub pages deployment config.
  organizationName: GITHUB_ORG,
  projectName: GITHUB_REPO,

  onBrokenLinks: 'throw',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: `${GITHUB_URL}/tree/main/docs-site/`,
        },
        // Blog is intentionally disabled for now — the default Docusaurus demo
        // posts were removed. Re-enable (and add a `blog/` dir) when we start
        // publishing release notes.
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
        // SEO: emit sitemap.xml so search engines can crawl every page.
        // Submit this URL directly in Search Console (project sites can't rely
        // on a root robots.txt — see static/robots.txt).
        sitemap: {
          lastmod: 'date',
          changefreq: 'weekly',
          priority: 0.5,
          ignorePatterns: ['/tags/**', '/search'],
          filename: 'sitemap.xml',
        },
        // GA4 traffic tracking. Only wired up when GA4_ID is set, so local
        // dev builds don't need it and CI stays the single source of the ID.
        ...(GA4_ID
          ? {gtag: {trackingID: GA4_ID, anonymizeIP: true}}
          : {}),
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Default social-share card (Open Graph / Twitter). TODO: replace this
    // Docusaurus placeholder with a branded 1200×630 card for rich previews.
    image: 'img/docusaurus-social-card.jpg',
    // Site-wide SEO metadata. Per-page <title>/description still come from
    // each doc's frontmatter; these are the global defaults + keywords.
    metadata: [
      {
        name: 'keywords',
        content:
          'playwright, e2e testing, self-healing tests, test automation, flaky tests, ' +
          'selector healing, qa automation, ci, github action, langgraph, ai testing',
      },
      {name: 'description', content: SITE_DESCRIPTION},
      {property: 'og:type', content: 'website'},
      {name: 'twitter:card', content: 'summary_large_image'},
    ],
    // Dark-mode-first (see docs-site/DESIGN.md). Always start in dark;
    // the toggle stays available, but we don't defer to the OS setting.
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'E2E-Healer',
      logo: {
        alt: 'E2E-Healer Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: GITHUB_URL,
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/getting-started/introduction',
            },
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'Contributing',
              href: `${GITHUB_URL}/blob/main/CONTRIBUTING.md`,
            },
            {
              label: 'Code of Conduct',
              href: `${GITHUB_URL}/blob/main/CODE_OF_CONDUCT.md`,
            },
            {
              label: 'Security',
              href: `${GITHUB_URL}/blob/main/SECURITY.md`,
            },
            {
              label: 'License',
              href: `${GITHUB_URL}/blob/main/LICENSE`,
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: GITHUB_URL,
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} E2E-Healer. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
