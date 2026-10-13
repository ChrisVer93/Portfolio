# Christian Verrecchia — Engineering Portfolio

A responsive portfolio presenting power electronics, magnetics, embedded electronics and validation work, with direct access to Converter Loss Lab.

## Website

Current live site: https://christian-verrecchia-portfolio.secretcrab1.chatgpt.site

Converter Loss Lab: https://christian-converter-loss-lab.secretcrab1.chatgpt.site

## Structure

- `dist/index.html` — portfolio content and semantic layout
- `dist/style.css` — responsive styling
- `dist/app.js` — mobile navigation, project filters and project details
- `.github/workflows/pages.yml` — deployment to GitHub Pages

The portfolio is plain HTML, CSS and JavaScript. It needs no dependencies, build step, database or application server. The calculation app stays in a separate maintained codebase; the portfolio links to it.

## GitHub Pages

For a profile website, use a repository named `<your-username>.github.io`. For a project website, use a name such as `engineering-portfolio`. Both layouts work because local asset URLs are relative.

In the repository settings, select **Pages → Build and deployment → Source: GitHub Actions**. Push the source to the `main` branch. The included workflow uploads `dist/` and deploys the site.

A custom domain can be configured in GitHub Pages settings later without rewriting the site.

## Editing

Update text and project content in `dist/index.html` and the project-detail entries in `dist/app.js`. Contact details are intentionally omitted until a public address or profile is provided. Illustrative graphics are explicitly labelled; the portfolio does not present them as measured results.

## Verification

JavaScript syntax, unique HTML IDs, section-link targets and local asset presence were checked. Browser visual testing was unavailable in the creation environment.
