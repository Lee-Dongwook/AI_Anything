import React, { type ReactNode } from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import HelpWantedBoard from '@site/src/components/HelpWantedBoard';

import styles from './index.module.css';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={styles.hero}>
      <div className={styles.contentContainer}>
        <Heading as="h1" className={styles.heroTitle}>
          Self-healing E2E tests
        </Heading>
        {/* DESIGN §3.1: One-line subtitle using --eeh-text-muted */}
        <p className={styles.heroSubtitle}>
          {siteConfig.tagline}
        </p>
        <div className={styles.heroActions}>
          <Link
            className={`${styles.ctaButton} ${styles.ctaPrimary}`}
            to="/docs/getting-started/introduction">
            Get Started
          </Link>
          <Link
            className={`${styles.ctaButton} ${styles.ctaSecondary}`}
            to="https://github.com/Lee-Dongwook/E2E-Self-Heal">
            ★ Star on GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

function ValueProps() {
  return (
    <section className={styles.features}>
      <div className={styles.featuresGrid}>
        {/* Placeholder text as requested: "maintainer will provide final copy" */}
        <div className={styles.featureCard}>
          <Heading as="h3" className={styles.featureTitle}>Value Prop 1</Heading>
          <p className={styles.featureText}>Maintainer will provide final copy here.</p>
        </div>
        <div className={styles.featureCard}>
          <Heading as="h3" className={styles.featureTitle}>Value Prop 2</Heading>
          <p className={styles.featureText}>Maintainer will provide final copy here.</p>
        </div>
        <div className={styles.featureCard}>
          <Heading as="h3" className={styles.featureTitle}>Value Prop 3</Heading>
          <p className={styles.featureText}>Maintainer will provide final copy here.</p>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} — Self-healing Playwright E2E tests`}
      description="Auto-repair broken Playwright E2E tests with an AI agent. When a UI change breaks a selector, E2E-Healer diagnoses, patches the locator, verifies it against the live DOM, and re-runs until green — as a local CLI or a CI GitHub Action that opens a patch PR.">

      <main className={styles.mainContent}>
        <HomepageHeader />
        <ValueProps />
        
        {/* Kept intact: HelpWantedBoard is part of the DESIGN.md wireframe */}
        <section className={styles.helpWantedSection}>
          <div className={styles.contentContainer}>
            <div className={styles.sectionHeader}>
              <Heading as="h2" className={styles.sectionTitle}>
                Help Wanted
              </Heading>
              <p className={styles.sectionSubtitle}>
                Want to help build self-healing test tools? Choose a component area below to find open GitHub issues.
              </p>
            </div>
            <HelpWantedBoard />
          </div>
        </section>
      </main>
    </Layout>
  );
}
