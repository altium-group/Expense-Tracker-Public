function copy(sharecode) {

  navigator.clipboard.writeText('https://127.0.0.1:5000/sharecode/' + sharecode);

  alert("Code copié");
}