#!/usr/bin/env node

var packer = require('node.packer');

function pack(eventType, filename) {
  input = ['js/libs/jquery-2.1.4.min.js'] 
  input.unshift(filename)

  if (filename.includes('journalist')) {
    output = 'static/js/journalist.js'
  } else {
    output = 'static/js/source.js'
  }
    
  packer({
    log : true,
    minify: true,
    uglify: false,
    input: input,
    output: output,
    callback: function ( err, code ){
      err && console.log( err );
    }
  });
}

fs.watch('js/source.js', pack)
fs.watch('js/journalist.js', pack)
