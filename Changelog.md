# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2019-08-11
### Added
- A changelog.
- Better handling of Saxon output to stop processing on unrecoverable errors.
- Handle resources that are referenced with a URL.
- Cache keeps historical versions in stead of removing earlier versions.

### Changed
- Result names are no longer defined by the input file-name, but is a sha of the file
  content and the XSLT used to convert the file.
- When cache is disabled, output the result to the current working directory. 
