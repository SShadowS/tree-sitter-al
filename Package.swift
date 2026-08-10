// swift-tools-version:5.3
import PackageDescription

let package = Package(
    name: "TreeSitterAl",
    products: [
        .library(name: "TreeSitterAl", targets: ["TreeSitterAl"]),
    ],
    dependencies: [
        .package(url: "https://github.com/ChimeHQ/SwiftTreeSitter", from: "0.8.0"),
    ],
    targets: [
        .target(
            name: "TreeSitterAl",
            dependencies: [],
            path: ".",
            sources: [
                "src/parser.c",
                // REQUIRED. This grammar has had an external scanner for its
                // entire life and eight tokens depend on it: PROPERTY_NAME,
                // CONTINUE_AS_IDENTIFIER, PREPROC_OPEN/CLOSE,
                // BEGIN_KEYWORD/END_KEYWORD and both PREPROC_SPLIT_*. Without
                // it the package does not link -- parser.c references five
                // tree_sitter_al_external_scanner_* symbols that live only
                // here. Verified by linking parser.c alone: all five come back
                // undefined. This line was the tree-sitter template's
                // "add it here" placeholder, left unedited, so the published
                // Swift package could never have worked.
                "src/scanner.c",
            ],
            resources: [
                .copy("queries")
            ],
            publicHeadersPath: "bindings/swift",
            cSettings: [.headerSearchPath("src")]
        ),
        .testTarget(
            name: "TreeSitterAlTests",
            dependencies: [
                "SwiftTreeSitter",
                "TreeSitterAl",
            ],
            path: "bindings/swift/TreeSitterAlTests"
        )
    ],
    cLanguageStandard: .c11
)
