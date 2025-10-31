use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashSet;

/// Input data for a single bibliographic item
#[derive(Debug, FromPyObject)]
struct ItemData {
    #[pyo3(item)]
    item_index: usize,
    #[pyo3(item)]
    doi: Option<String>,
    #[pyo3(item)]
    title: String,
    #[pyo3(item)]
    author_surnames: Vec<String>,
    #[pyo3(item)]
    year: Option<i32>,
    #[pyo3(item)]
    journal_name: Option<String>,
}

/// Output index data structure
#[pyclass]
struct IndexData {
    #[pyo3(get)]
    doi_to_index: Py<PyDict>,
    #[pyo3(get)]
    trigram_to_indices: Py<PyDict>,
    #[pyo3(get)]
    surname_to_indices: Py<PyDict>,
    #[pyo3(get)]
    decade_to_indices: Py<PyDict>,
    #[pyo3(get)]
    journal_to_indices: Py<PyDict>,
}

/// Extract trigrams from text
fn extract_trigrams(text: &str) -> HashSet<String> {
    let normalized = text.to_lowercase();
    let chars: Vec<char> = normalized.chars().collect();

    if chars.len() < 3 {
        return HashSet::new();
    }

    let mut trigrams = HashSet::new();
    for i in 0..=chars.len() - 3 {
        let trigram: String = chars[i..i + 3].iter().collect();
        trigrams.insert(trigram);
    }

    trigrams
}

/// Calculate decade from year
fn get_decade(year: Option<i32>) -> Option<i32> {
    year.map(|y| (y / 10) * 10)
}

/// Build index for fuzzy matching
#[pyfunction]
fn build_index_rust(py: Python, items_data: Vec<ItemData>) -> PyResult<IndexData> {
    use ahash::AHashMap;

    // Pre-allocate with capacity hints
    let capacity = items_data.len();
    let mut doi_map: AHashMap<String, usize> = AHashMap::with_capacity(capacity);
    let mut trigram_map: AHashMap<String, Vec<usize>> = AHashMap::new();
    let mut surname_map: AHashMap<String, Vec<usize>> = AHashMap::new();
    let mut decade_map: AHashMap<Option<i32>, Vec<usize>> = AHashMap::new();
    let mut journal_map: AHashMap<String, Vec<usize>> = AHashMap::new();

    // Single pass over all items
    for item in items_data {
        let idx = item.item_index;

        // DOI index
        if let Some(doi) = item.doi {
            doi_map.insert(doi, idx);
        }

        // Title trigram index
        let trigrams = extract_trigrams(&item.title);
        for trigram in trigrams {
            trigram_map.entry(trigram).or_insert_with(Vec::new).push(idx);
        }

        // Author surname index
        for surname in item.author_surnames {
            let normalized = surname.to_lowercase().trim().to_string();
            if !normalized.is_empty() {
                surname_map.entry(normalized).or_insert_with(Vec::new).push(idx);
            }
        }

        // Year decade index
        let decade = get_decade(item.year);
        decade_map.entry(decade).or_insert_with(Vec::new).push(idx);

        // Journal index
        if let Some(journal) = item.journal_name {
            let normalized = journal.to_lowercase().trim().to_string();
            if !normalized.is_empty() {
                journal_map.entry(normalized).or_insert_with(Vec::new).push(idx);
            }
        }
    }

    // Convert to Python dicts
    let doi_dict = PyDict::new_bound(py);
    for (k, v) in doi_map {
        doi_dict.set_item(k, v)?;
    }

    let trigram_dict = PyDict::new_bound(py);
    for (k, v) in trigram_map {
        let py_list = PyList::new_bound(py, &v);
        trigram_dict.set_item(k, py_list)?;
    }

    let surname_dict = PyDict::new_bound(py);
    for (k, v) in surname_map {
        let py_list = PyList::new_bound(py, &v);
        surname_dict.set_item(k, py_list)?;
    }

    let decade_dict = PyDict::new_bound(py);
    for (k, v) in decade_map {
        let py_list = PyList::new_bound(py, &v);
        decade_dict.set_item(k, py_list)?;
    }

    let journal_dict = PyDict::new_bound(py);
    for (k, v) in journal_map {
        let py_list = PyList::new_bound(py, &v);
        journal_dict.set_item(k, py_list)?;
    }

    Ok(IndexData {
        doi_to_index: doi_dict.into(),
        trigram_to_indices: trigram_dict.into(),
        surname_to_indices: surname_dict.into(),
        decade_to_indices: decade_dict.into(),
        journal_to_indices: journal_dict.into(),
    })
}

/// A simple test function to verify Rust integration works
#[pyfunction]
fn hello_rust() -> PyResult<String> {
    Ok("Hello from Rust!".to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_rust, m)?)?;
    m.add_function(wrap_pyfunction!(build_index_rust, m)?)?;
    m.add_class::<IndexData>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_trigrams() {
        let text = "hello";
        let trigrams = extract_trigrams(text);

        assert_eq!(trigrams.len(), 3);
        assert!(trigrams.contains("hel"));
        assert!(trigrams.contains("ell"));
        assert!(trigrams.contains("llo"));
    }

    #[test]
    fn test_extract_trigrams_short() {
        let text = "hi";
        let trigrams = extract_trigrams(text);
        assert_eq!(trigrams.len(), 0);
    }

    #[test]
    fn test_get_decade() {
        assert_eq!(get_decade(Some(1995)), Some(1990));
        assert_eq!(get_decade(Some(2000)), Some(2000));
        assert_eq!(get_decade(Some(2025)), Some(2020));
        assert_eq!(get_decade(None), None);
    }
}
