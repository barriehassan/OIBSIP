# Design notes

## Problem and scope

Create unique passwords with explicit length and character rules, useful feedback, and an approachable desktop interface. No account, database, network API, or saved password file is needed.

## Flow

Input settings → validate length and category count → build filtered alphabets → sample with OS-backed randomness → reject candidates missing a required category → return accepted password → update strength and memory history → copy only when requested or enabled.

Every enabled alphabet is disjoint, and every position is sampled independently from their union. Rejection leaves the accepted strings uniformly distributed over the subset satisfying the category rule. There is deliberately no fixed retry limit that could return an invalid password.

## Responsibilities

Core modules have no GUI dependency. The controller owns current output and a bounded deque of five recent values. The desktop owns visual state and passes validated options to the controller. Clipboard access is isolated and returns a result rather than crashing when the OS clipboard is unavailable. CLI imports only core modules and the standard library.

## Tradeoffs

Length 8 is supported for the exercise; the default is 18. Requiring two categories is a project rule, not a claim that all single-category passwords are insecure. The strength estimate is an upper bound, not a measured attack time. In-memory history improves convenience but keeps sensitive values alive until cleared or closed. Rejection sampling may repeat; with these alphabets and minimum length its expected cost is small. Python strings cannot be reliably zeroed.

## Learning outcomes

Dataclasses, validation and exceptions, secure random sampling, separation of concerns, bounded collections, event-driven GUI programming, dependency management, automated testing, and honest documentation of validation limits.

## Mountain-glass rendering

The landscape supplied with the project is fitted to the window. Pillow blurs a copy, tints rounded panel regions, and composites them onto the scene. The image is rebuilt only when window dimensions change; updates redraw canvas controls against the cached image. Two persistent native Tk entry widgets provide selection, copying and numeric editing without being destroyed on redraw. Standard Tk and available system fonts support Tk 8.6/9 without requiring CustomTkinter.
