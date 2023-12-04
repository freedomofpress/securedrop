use pyo3::types::PyBytes;
use pyo3::{intern, PyAny, PyResult};
use std::io::{self, ErrorKind, Read, Write};

/// Wrapper to implement the `Read` trait around a Python
/// object that contains a `.read()` function.
pub(crate) struct Stream<'a> {
    pub(crate) reader: &'a PyAny,
}

impl Stream<'_> {
    /// Read the specified number of bytes out of the object
    fn read_bytes(&self, len: usize) -> PyResult<&PyBytes> {
        let func = self.reader.getattr(intern!(self.reader.py(), "read"))?;
        // In Python this is effectively calling `reader.read(len)`
        let bytes = func.call1((len,))?;
        let bytes = bytes.downcast::<PyBytes>()?;
        Ok(bytes)
    }
}

impl Read for Stream<'_> {
    fn read(&mut self, mut buf: &mut [u8]) -> std::io::Result<usize> {
        let bytes = self.read_bytes(buf.len()).map_err(|err| {
            // The PyErr could be a type error (e.g. no "read" method) or an
            // actual I/O failure if the read() call failed, let's just treat
            // all of them as "other" for simplicity.
            io::Error::new(ErrorKind::Other, err.to_string())
        })?;
        buf.write(bytes.as_bytes())
    }
}
