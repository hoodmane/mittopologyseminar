var readline = require('readline');
var mjAPI = require("mathjax-node");

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


mjAPI.config({
  MathJax: {
    TeX: { 
        extensions: ["begingroup.js"],
        Macros: macros
    }
  }
});
mjAPI.start();

var rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', function(line){
    mjAPI.typeset({
      math: line,
      format: "TeX", // "inline-TeX", "MathML"
      html:true, //  svg:true,
      speakText: false
    }, function (data) {
      if(!line.startsWith("\\begingroup") && !line.startsWith("\\endgroup")) {
          if (!data.errors) {
                console.log(data.html + "\ndone\n");
          }
      }
    });
})
