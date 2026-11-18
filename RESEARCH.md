# Scope and evidence

The checker is a conservative static HTML heuristic, intended as one lightweight review signal. Its rule-to-criterion links point to WCAG 2.2: text alternatives (1.1.1), information and relationships (1.3.1), headings and labels (2.4.6), and name/role/value (4.1.2). A machine scan cannot determine whether alternative text is meaningful, whether a control's label is understandable, or whether the complete page conforms.

Evidence:
- [W3C Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/)
- [W3C Understanding 1.1.1 Non-text Content](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html)
- [W3C Understanding 4.1.2 Name, Role, Value](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html)
- [W3C ARIA Authoring Practices: landmarks](https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/)

Limits: only one local HTML document is inspected; external labels/scripts, computed accessible names, shadow DOM, CSS visibility, iframe content, keyboard operation, contrast, and actual assistive-technology behavior are out of scope. An observed main landmark or a syntactically named control does not establish WCAG conformance.
