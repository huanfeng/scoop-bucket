# huanfeng's Scoop Bucket

[![Tests](https://github.com/huanfeng/scoop-bucket/actions/workflows/ci.yml/badge.svg)](https://github.com/huanfeng/scoop-bucket/actions/workflows/ci.yml) [![Excavator](https://github.com/huanfeng/scoop-bucket/actions/workflows/excavator.yml/badge.svg)](https://github.com/huanfeng/scoop-bucket/actions/workflows/excavator.yml)

Scoop bucket for [huanfeng](https://github.com/huanfeng)'s command-line tools.

## Installation

```pwsh
# Add the bucket
scoop bucket add huanfeng https://github.com/huanfeng/scoop-bucket

# Install an app
scoop install huanfeng/apkhub

# Verify installation
apkhub version
```

## Update

```pwsh
scoop update apkhub
```

## Available Apps

- **apk_info_tool** - View APK/XAPK/APKM file information and install them
- **apkhub** - A command-line tool for managing distributed APK repositories
- **hex** - Base converter and calculator
- **lsuart** - Command-line serial port lister
- **setadb** - Switch the ADB target device by setting `ANDROID_SERIAL`

### Note on setadb

`setadb` changes an environment variable, so it must run *inside* your shell
rather than in a child process. In CMD it works out of the box. In PowerShell,
run this once so that plain `setadb` resolves to the PowerShell version:

```pwsh
& "$(scoop prefix setadb)\install-profile.ps1"
```

Without it, `setadb` resolves to `setadb.bat` (PATHEXT ranks `.BAT` above
`.PS1`), which runs in a throw-away `cmd.exe` and has no lasting effect. The
script detects this and warns rather than failing silently.

## How do I contribute new manifests?

To make a new manifest contribution, please read the [Contributing
Guide](https://github.com/ScoopInstaller/.github/blob/main/.github/CONTRIBUTING.md)
and [App Manifests](https://github.com/ScoopInstaller/Scoop/wiki/App-Manifests)
wiki page.
