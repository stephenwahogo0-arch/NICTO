use std::collections::HashMap;

use pyo3::prelude::*;

/// Sector 6 extension — WebForge: static site generator, template rendering, deploy orchestration.
#[pyclass]
pub struct WebForge {
    templates: HashMap<String, String>,
    sites: HashMap<String, SiteConfig>,
}

#[derive(Clone, Debug)]
struct SiteConfig {
    domain: String,
    template: String,
    variables: HashMap<String, String>,
    output_dir: String,
}

#[pymethods]
impl WebForge {
    #[new]
    pub fn new() -> Self {
        Self { templates: HashMap::new(), sites: HashMap::new() }
    }

    pub fn add_template(&mut self, name: &str, content: &str) {
        self.templates.insert(name.into(), content.into());
    }

    pub fn add_site(&mut self, name: &str, domain: &str,
                     template: &str, output_dir: &str, variables: HashMap<String, String>) -> PyResult<()> {
        if !self.templates.contains_key(template) {
            return Err(pyo3::exceptions::PyKeyError::new_err(
                format!("template '{}' not found", template)));
        }
        self.sites.insert(name.into(), SiteConfig {
            domain: domain.into(), template: template.into(),
            variables, output_dir: output_dir.into(),
        });
        Ok(())
    }

    pub fn render(&self, site_name: &str) -> PyResult<String> {
        let site = self.sites.get(site_name)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(
                format!("site '{}' not found", site_name)))?;
        let tpl = self.templates.get(&site.template).unwrap();
        let mut html = tpl.clone();
        for (k, v) in &site.variables {
            html = html.replace(&format!("{{{{{}}}}}", k), v);
        }
        Ok(html)
    }

    pub fn list_sites(&self) -> Vec<String> {
        self.sites.keys().cloned().collect()
    }

    pub fn list_templates(&self) -> Vec<String> {
        self.templates.keys().cloned().collect()
    }
}
