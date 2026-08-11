cmake_minimum_required(VERSION 3.13)

project(tree-sitter-al
        VERSION "0.1.0"
        DESCRIPTION "AL for Business Central"
        HOMEPAGE_URL "https://github.com/sshadows/tree-sitter-al"
        LANGUAGES C)

option(BUILD_SHARED_LIBS "Build using shared libraries" ON)
option(TREE_SITTER_REUSE_ALLOCATOR "Reuse the library allocator" OFF)

# 15, matching the committed src/parser.c's LANGUAGE_VERSION. It said 14, which
# labelled an ABI-15 parser as 14 -- so this is a correction, not a break. Note
# SOVERSION below is derived from it and moves with it.
set(TREE_SITTER_ABI_VERSION 15 CACHE STRING "Tree-sitter ABI version")
if(NOT ${TREE_SITTER_ABI_VERSION} MATCHES "^[0-9]+$")
    unset(TREE_SITTER_ABI_VERSION CACHE)
    message(FATAL_ERROR "TREE_SITTER_ABI_VERSION must be an integer")
endif()

# THE IN-SOURCE GENERATE STEP IS GONE, AND MUST NOT COME BACK.
#
# There used to be an add_custom_command whose OUTPUT was
# "${CMAKE_CURRENT_SOURCE_DIR}/src/parser.c", running `tree-sitter generate
# --abi=${TREE_SITTER_ABI_VERSION}` in the source tree. A BUILD MUST NOT MUTATE
# TRACKED FILES. src/parser.c is committed and authoritative, and CI regenerates
# it and runs `git diff --exit-code`, so a build that silently rewrites it turns
# "I built the project" into an uncommitted change nobody chose.
#
# It was not hypothetical: configuring and building this project once, to check
# that scanner.c was compiled, rewrote the committed parser.c from
# LANGUAGE_VERSION 15 down to 14 and swapped TSLexerMode back to TSLexMode. It
# was caught only by reading `git status` afterwards.
#
# Regenerating is a developer action (`tree-sitter generate`), not a build step,
# and the committed parser makes it unnecessary here. If a generate step is ever
# genuinely wanted, it must write into ${CMAKE_CURRENT_BINARY_DIR} and the
# library must be built from that copy -- never back into src/.

# scanner.c is UNCONDITIONAL, and the guard it replaces was two hazards.
#
# It was `if(EXISTS src/scanner.c)`. CMake documents if(EXISTS) as well-defined
# only for FULL paths -- a relative one is undefined behaviour. It happens to
# evaluate TRUE on CMake 3.29.2 (measured), so the build works today, but the
# whole construct is wrong in a more basic way: this grammar has had an external
# scanner for its entire life, so a missing scanner.c is not a configuration to
# degrade gracefully into. It is a broken checkout.
#
# Degrading silently is the worse failure: parser.c references five
# tree_sitter_al_external_scanner_* symbols, so skipping scanner.c does not
# produce a scanner-less parser, it produces a library that cannot link -- and
# the diagnostic then points at undefined symbols rather than at the missing
# file. Listing it unconditionally makes CMake say which file is absent.
add_library(tree-sitter-al src/parser.c src/scanner.c)
target_include_directories(tree-sitter-al PRIVATE src)

target_compile_definitions(tree-sitter-al PRIVATE
                           $<$<BOOL:${TREE_SITTER_REUSE_ALLOCATOR}>:TREE_SITTER_REUSE_ALLOCATOR>
                           $<$<CONFIG:Debug>:TREE_SITTER_DEBUG>)

set_target_properties(tree-sitter-al
                      PROPERTIES
                      C_STANDARD 11
                      POSITION_INDEPENDENT_CODE ON
                      SOVERSION "${TREE_SITTER_ABI_VERSION}.${PROJECT_VERSION_MAJOR}"
                      DEFINE_SYMBOL "")

configure_file(bindings/c/tree-sitter-al.pc.in
               "${CMAKE_CURRENT_BINARY_DIR}/tree-sitter-al.pc" @ONLY)

include(GNUInstallDirs)

install(FILES bindings/c/tree-sitter-al.h
        DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/tree_sitter")
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/tree-sitter-al.pc"
        DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/pkgconfig")
install(TARGETS tree-sitter-al
        LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}")

add_custom_target(test "${TREE_SITTER_CLI}" test
                  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
                  COMMENT "tree-sitter test")

# vim:ft=cmake:
