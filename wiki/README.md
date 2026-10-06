# Vivan wiki source

This directory contains the source for the project's GitHub wiki:

| File | Published role |
|---|---|
| [Home.md](Home.md) | Wiki landing page |
| [Case-Study-Blog.md](Case-Study-Blog.md) | Complete Vivan technical case study |
| [_Sidebar.md](_Sidebar.md) | Wiki navigation |
| [_Footer.md](_Footer.md) | Shared wiki footer |
| [publish.ps1](publish.ps1) | Publishes these four files to GitHub's separate wiki repository |

The article describes Vivan's move from decentralized e-commerce data to a centralized Azure Databricks lakehouse and purchase-propensity modeling. It uses the provided reference blog's narrative structure, with this project's implementation details and recorded evidence.

## First-time wiki initialization

GitHub stores wiki pages in a separate Git repository. Saving files in this main repository does not publish the wiki. The first page must be created on GitHub before its wiki Git endpoint is available, as described in the [official wiki instructions](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages#cloning-wikis-to-your-computer).

1. Open [Create first page](https://github.com/Muhammad-Hamza69/Databricks-Azure-Fintech-Case-Study/wiki/_new).
2. Use title **Home** and body `Vivan e-commerce data platform`.
3. Click **Save Page**.

## Publish or update

From the main repository root, with Git installed and GitHub write access configured:

```powershell
& .\wiki\publish.ps1
```

The script detects the wiki's default branch, clones it into the ignored `.git-recovery/` directory, backs up its previous history, replaces the four prepared pages, and performs a normal commit and push. It preserves other wiki files and does not force-push. The page links without `.md` extensions are intended for GitHub wiki navigation.

After successful publication, open [Vivan Case Study Blog](https://github.com/Muhammad-Hamza69/Databricks-Azure-Fintech-Case-Study/wiki/Case-Study-Blog).

Architecture images reference the PNG already committed to the main project repository. Large datasets and secrets are not copied into the wiki.
