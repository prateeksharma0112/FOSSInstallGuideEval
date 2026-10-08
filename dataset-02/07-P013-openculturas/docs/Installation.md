## Requirements
* https://www.drupal.org/docs/system-requirements for Drupal
  * PHP 8.4
* A bunch of drupal modules and external libraries.

## Installation

### New installation

Use the composer project template:

```bash
composer create-project --remove-vcs drupal/openculturas_project example.org
```

For more information go to https://www.drupal.org/project/openculturas_project.

### Updating

#### Patch release

Optionally update library versions in the inline package repositories in `composer.json`, then:

```bash
composer update openculturas/openculturas-distribution "drupal/core-*" drupal/core --with-dependencies --minimal-changes
drush updatedb --yes
# Review changes, then export and commit configuration
drush config:export --yes
```

#### Minor release

Manually increase the version constraints for `drupal/core-*` and `openculturas/openculturas-distribution` to the next minor version in `composer.json`, then follow the same steps as a patch release.


## Development

Please read the [Development guidelines](DEVELOPMENT.md) before you start.

We recommend using https://ddev.com for development.

### Installation (with ddev)

* Clone this repository
* Install dependencies
  * `ddev composer install`
* Install OpenCulturas distribution
  * `ddev drush site:install --yes --existing-config`

### DDEV

Cheatsheet:

* Start project `ddev start`
* Run composer commands `ddev composer COMMAND` e.g. `ddev composer install`
* Run drush commands `ddev drush COMMAND` e.g. `ddev drush uli`
* Import latest database snapshot `ddev dbimport`

More information about ddev cli command https://ddev.readthedocs.io/en/stable/users/basics/cli-usage/.

### Patching

Patches are managed with [cweagans/composer-patches](https://docs.cweagans.net/composer-patches/) v2 and tracked in `patches.lock.json`.

```bash
ddev composer patches-relock   # Re-discover patches in composer.json and rewrite patches.lock.json
ddev composer patches-repatch  # Delete, re-download and re-apply patches for all affected packages
ddev composer patches-doctor   # Diagnose common patching issues
```

Run `patches-relock` after adding or removing a patch in `composer.json`. Run `patches-repatch` when a patch fails to apply or a package needs a clean re-install.

### PHP Quality Checks

```bash
ddev composer run php:lint        # PHP parallel lint
ddev composer run php:cs          # PHPCS
ddev composer run php:cs-fix      # Auto-fix PHPCS issues
ddev composer run php:phpstan     # Static analysis
ddev composer run php:rector      # Rector dry-run
ddev composer run php:rector-fix  # Rector auto-fix
```

### JS/CSS Linting

All linting commands run inside the DDEV container:

```bash
ddev exec npm run lint:js         # ESLint JavaScript (entire project)
ddev exec npm run lint:yaml       # ESLint YAML
ddev exec npm run lint:css        # stylelint CSS (profile/modules)
ddev exec npm run lint:css:fix    # Auto-fix CSS
ddev exec npm run lint:scss       # stylelint SCSS (openculturas_base theme)
ddev exec npm run lint:scss:fix   # Auto-fix SCSS
ddev exec npm run prettier        # Prettier JavaScript
ddev exec npm run prettier:css    # Prettier CSS
ddev exec npm run prettier:scss   # Prettier SCSS
```

To lint specific JS files:

```bash
ddev exec npx eslint --ext .js --no-ignore path/to/file.js
```

### Configuration files

All configurations are managed via [config_devel](https://www.drupal.org/project/config_devel).
Each configuration is listed in the info file of the profile or module.
Therefore, any changes to the configuration must also be made in the info file.

After that, enable config_devel and run `ddev composer run cde` or `ddev drush cde module`.

This command updates all configuration listed in the info file and removes the key `_core` and `uuid` except for
views configuration. The uuid is needed because the uuid is used in other configuration as a default value, without this
the default value would be not set/broken.
