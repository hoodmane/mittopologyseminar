macros={
    N: "\\mathbb{N}",
	Z: "\\mathbb{Z}",
    Q: "\\mathbb{Q}",
	R: "\\mathbb{R}",
	C: "\\mathbb{C}",
	H: "\\mathbb{H}",
	A: "\\mathbb{A}",
    infinity: "\\infty"
};

for (var i = 65; i <= 90; i++) {
    c = String.fromCharCode(i);
    macros[c+"bb"] = "\\mathbb{" + c + "}"
}


MathJax.Hub.Config({
    tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']], displayMath: [ ['$$','$$'], ['\[','\]'] ]},
	TeX: { 
        extensions: ["begingroup.js"],
        Macros: macros
    },
    "HTML-CSS": {
      scale: 80
    }
});
MathJax.Hub.Configured();
