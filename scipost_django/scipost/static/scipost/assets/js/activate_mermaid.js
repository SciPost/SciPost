import mermaid from 'mermaid'

mermaid.initialize({ startOnLoad: false });
document.body.addEventListener("htmx:afterSettle", function(evt) {
    mermaid.init(".workflowDiagram");
});
