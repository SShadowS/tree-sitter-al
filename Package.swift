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
                // NOTE: if your language has an external scanner, add it here.
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
