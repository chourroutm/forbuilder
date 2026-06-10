# Feature Specification: FORBILD Phantom Package

**Feature Branch**: `001-forbild-phantom-package`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "Build a small Python package that creates a digital phantom based on the FORBILD specifications"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Standard Phantom (Priority: P1)

A medical imaging researcher needs a standard FORBILD head phantom array to evaluate or
benchmark an image reconstruction algorithm. They call the package with desired spatial
dimensions and receive a 3D array where each voxel encodes the attenuation value of the
corresponding tissue component as defined by the FORBILD specification.

**Why this priority**: This is the core deliverable of the package. Without it, no other
story provides value. It directly enables CT algorithm benchmarking and scanner evaluation
workflows that the package exists to support.

**Independent Test**: Can be fully tested by calling the phantom-generation entry point with
standard parameters and verifying the returned array has the correct shape, value range, and
matches reference FORBILD phantom data within tolerance.

**Acceptance Scenarios**:

1. **Given** a researcher requests a phantom with default spatial parameters, **When** they
   call the generation function, **Then** they receive a 3D array of unsigned 8-bit integers
   whose shape matches the requested dimensions and whose values fall within the expected
   range for FORBILD-specified tissue types.

2. **Given** a researcher requests a phantom at a specific voxel size (e.g., 0.5 mm
   isotropic), **When** the function executes, **Then** the output array dimensions are
   consistent with the requested physical volume and voxel size.

3. **Given** a researcher calls the generation function twice with identical parameters,
   **When** the results are compared, **Then** both arrays are bit-for-bit identical
   (deterministic output).

4. **Given** a researcher provides invalid parameters (e.g., a negative array dimension or
   a voxel size of zero), **When** the function is called, **Then** it raises a descriptive
   error that identifies the invalid parameter, its value, and the valid range.

---

### User Story 2 - Inspect Phantom Components (Priority: P2)

A researcher wants to understand what geometric objects make up the phantom without
generating the full 3D array. They query the package for the list of FORBILD components
(ellipsoids, cylinders, etc.) and inspect each component's position, size, orientation,
and assigned attenuation value.

**Why this priority**: Enables validation, documentation, and selective use of the phantom
geometry. Researchers often need to verify that a specific region-of-interest corresponds
to a known component before running numerical experiments.

**Independent Test**: Can be tested by retrieving the component list and verifying it
contains the expected number of FORBILD-defined objects, each with the correct geometry
attributes and attenuation values as specified in the FORBILD reference document.

**Acceptance Scenarios**:

1. **Given** a researcher calls the component-query entry point, **When** the result is
   returned, **Then** it is a collection of component descriptions each containing: a name,
   a geometric type (e.g., ellipsoid), spatial parameters (centre, semi-axes, orientation),
   and the assigned attenuation value.

2. **Given** a researcher selects a specific component by name, **When** they retrieve its
   geometry, **Then** the values match the published FORBILD specification exactly (not an
   approximation).

3. **Given** a researcher modifies a component's attenuation value before generating the
   phantom, **When** the array is produced, **Then** only the voxels belonging to that
   component reflect the modified value while all others remain at their standard values.

---

### User Story 3 - Extract 2D Slices (Priority: P3)

A researcher wants to inspect a single 2D cross-section of the phantom (axial, coronal, or
sagittal) to visually verify the phantom geometry or to generate 2D test inputs for a 2D
reconstruction algorithm, without loading the full 3D array.

**Why this priority**: Reduces memory pressure for workflows that only need one plane.
Supports verification and 2D algorithm testing without requiring a full-volume generation,
making the package usable in memory-constrained environments.

**Independent Test**: Can be tested by extracting a slice at a known index and confirming
the 2D array has the correct shape, correct dtype, and that pixel values match the
corresponding layer of the full 3D array.

**Acceptance Scenarios**:

1. **Given** a researcher requests an axial slice at a specified index, **When** the slice
   is returned, **Then** it is a 2D array of unsigned 8-bit integers with shape equal to
   the phantom's row × column dimensions.

2. **Given** a researcher requests a coronal or sagittal slice, **When** the slice is
   returned, **Then** the orientation-specific dimensions are correct and pixel values
   match the corresponding voxels in the full 3D array.

3. **Given** a researcher requests a slice at an out-of-bounds index, **When** the request
   is made, **Then** a descriptive error is raised that states the requested index, the
   valid range, and the axis name.

---

### Edge Cases

- What happens when the requested array size is so small (e.g., 4×4×4 voxels) that no
  FORBILD component covers any voxel? The output MUST be a valid array filled with the
  background attenuation value, not an error.
- What happens when the requested voxel size is so large that all components overlap or
  are entirely outside the sampled volume? The package MUST return the correctly computed
  array and emit a warning that some components may be under-sampled or absent.
- What happens when the system has insufficient memory to allocate the requested array
  size? The package MUST propagate the system memory error without masking it.
- What happens when a component's modified attenuation value is outside the 0–255 range?
  The package MUST reject the value with a descriptive error before generation begins.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST provide a single entry point that generates and returns a
  3D array representing the standard FORBILD head phantom given spatial parameters.
- **FR-002**: The output array MUST be composed of unsigned 8-bit integer values where
  each value encodes the FORBILD-specified attenuation of the tissue type occupying that
  voxel.
- **FR-003**: Users MUST be able to specify the number of voxels along each spatial axis
  (rows, columns, slices) independently.
- **FR-004**: Users MUST be able to specify the isotropic or anisotropic voxel size in
  millimetres to control the physical extent of the sampled volume.
- **FR-005**: The package MUST provide a query entry point that returns the complete list
  of FORBILD phantom components with their geometry and attenuation attributes.
- **FR-006**: Users MUST be able to override the attenuation value of any individual
  component before generating the phantom, without altering the component's geometry.
- **FR-007**: The package MUST provide a slice-extraction entry point that returns a
  single 2D cross-section (axial, coronal, or sagittal) at a caller-specified index.
- **FR-008**: Generated phantom arrays MUST be numerically reproducible: identical inputs
  MUST always produce bit-for-bit identical outputs.
- **FR-009**: The package MUST validate all caller-supplied parameters at the point of
  entry and raise descriptive errors identifying the invalid parameter, its value, and the
  expected valid range.
- **FR-010**: The package MUST emit structured log messages during phantom generation
  (progress at key stages, warnings for under-sampled components, errors on failure).

### Key Entities

- **Phantom**: The complete volumetric representation — defined by spatial parameters
  (shape and voxel size) and composed of one or more components rasterized onto a voxel
  grid; carries the output 3D array.
- **Component**: A single geometric object in the FORBILD specification — characterized
  by a name, geometric type (ellipsoid, cylinder, sphere, or cone), spatial parameters
  (centre coordinates, semi-axes or radius, orientation angles), and an attenuation value.
- **VoxelGrid**: The discrete 3D sampling space into which all components are rasterized;
  defines the coordinate system used to map physical millimetre positions to voxel indices.
- **Slice**: A 2D cross-section of the phantom extracted at a specific index along one of
  the three spatial axes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A researcher can generate the standard FORBILD head phantom with a single
  function call using default parameters, with no additional configuration required.
- **SC-002**: Phantom generation for a 256×256×256 voxel array completes in under 60
  seconds on a standard single-core workstation.
- **SC-003**: Output voxel values match the FORBILD reference phantom data with a
  maximum absolute error of 1 grayscale unit (≤ 1 on a 0–255 scale) for every voxel.
- **SC-004**: The complete component list can be retrieved and inspected without
  generating any array data.
- **SC-005**: A single 2D slice can be extracted without allocating the full 3D array
  in memory.
- **SC-006**: All invalid input parameters are caught before computation begins, with
  error messages that identify the problem unambiguously.

## Assumptions

- The initial implementation targets the FORBILD head phantom only; the thorax and
  abdomen phantoms are out of scope for this version.
- The 8-bit value range (0–255) is mapped linearly from the minimum to maximum
  attenuation values defined in the FORBILD specification; the exact mapping constants
  are documented in the package.
- The package does not read from or write to files by default; it returns in-memory
  arrays and the caller is responsible for persistence.
- No GUI or visualization layer is included; researchers are expected to use their
  own preferred tools to render or inspect the output arrays.
- The target audience is medical imaging researchers and CT algorithm developers who
  are comfortable working with numerical arrays.
- The package is distributed as an installable library; no command-line interface is
  included in this version.
