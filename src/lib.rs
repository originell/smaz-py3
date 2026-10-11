mod codebook;
mod codec;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyString};

/// Compress a string into SMAZ bytes. Reject embedded NUL characters.
#[pyfunction(signature = (string, /))]
fn compress<'py>(py: Python<'py>, string: &Bound<'py, PyString>) -> PyResult<Bound<'py, PyBytes>> {
    let input = string.to_str()?.as_bytes();
    if input.contains(&0) {
        return Err(PyValueError::new_err("embedded null character"));
    }
    Ok(PyBytes::new(py, &codec::compress(input)))
}

/// Decode SMAZ bytes as UTF-8. Raise ValueError for truncated input.
#[pyfunction(signature = (bytes, /))]
fn decompress<'py>(py: Python<'py>, bytes: &Bound<'py, PyBytes>) -> PyResult<Bound<'py, PyString>> {
    let output = codec::decompress(bytes.as_bytes()).map_err(PyValueError::new_err)?;
    // Let Python validate UTF-8 once; validating in Rust as well doubles the
    // decoding work for non-ASCII output.
    PyString::from_bytes(py, &output)
}

#[pymodule]
fn smaz(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add(
        "_build_profile",
        if cfg!(debug_assertions) {
            "debug"
        } else {
            "release"
        },
    )?;
    module.add_function(wrap_pyfunction!(compress, module)?)?;
    module.add_function(wrap_pyfunction!(decompress, module)?)?;
    Ok(())
}
