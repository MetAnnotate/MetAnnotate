% import time
<!DOCTYPE HTML>
<!--
/*
 * jQuery File Upload Plugin Basic Demo 1.2.4
 * https://github.com/blueimp/jQuery-File-Upload
 *
 * Copyright 2013, Sebastian Tschan
 * https://blueimp.net
 *
 * Licensed under the MIT license:
 * http://www.opensource.org/licenses/MIT
 */
-->
<html lang="en">
<head>
<!-- Force latest IE rendering engine or ChromeFrame if installed -->
<!--[if IE]><meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"><![endif]-->
<meta charset="utf-8">
<title>metAnnotate</title>
<base href="/">
<meta name="description" content="todo">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Bootstrap styles -->
<link rel="stylesheet" href="./css/bootstrap.min.css">
<!-- CSS to style the file input field as button and adjust the Bootstrap progress bars -->
<link rel="stylesheet" href="./css/jquery.fileupload.css">
<link rel="stylesheet" href="./css/jquery-ui.css">
<link rel="stylesheet" href="./css/slider.css">
<link rel="stylesheet" href="./css/main.css?t={{time.time()}}">
<style>
.ui-menu-item {
  font-size: 12px;
  max-width: 300px;
}
div > .ui-menu {
  max-width: 300px;
}
.ui-menu-item {
  border: 1px solid #aaaaaa;
  border-width: 0 0 1px 0;
}
</style>
</head>
<body>
<div class="container">
  <div class="navbar navbar-default" role="navigation">
    <div class="container-fluid">
        <ul class="nav navbar-nav navbar-right">
          <li><a href="/">Welcome</a></li>
          <li><a href="/submit">Submit Job</a></li>
          <li><a href="/about/">About &amp; Help</a></li>
          <li><a href="/examples/">Example Analyses</a></li>
          <li><a href="/scripts/">Additional Analysis Scripts</a></li>
          <li><a href="/cite/">Cite</a></li>
          <li><a href="/contact/">Contact</a></li>
        </ul>
    </div><!--/.container-fluid -->
  </div>
  <div class="myborder">
    <h1><a href="./">metAnnotate</a></h1>
    <p>By
      <span style="color:red">Doxey</span><span style="color:gray">Lab</span>.
      Search, classify, and compare metagenomes.
    </p>
    <hr>
    %include
  </div>
</div>

<script src="./js/jquery.min.js"></script>
<!-- The jQuery UI widget factory, can be omitted if jQuery UI is already included -->
<script src="./js/jquery.ui.widget.js"></script>
<!-- The Iframe Transport is required for browsers without support for XHR file uploads -->
<script src="./js/jquery.iframe-transport.js"></script>
<!-- The basic File Upload plugin -->
<script src="./js/jquery.fileupload.js"></script>
<script src="./js/FileSaver.js"></script>
<script src="./js/jquery-ui.js"></script>
<!-- Bootstrap JS is not required, but included for the responsive demo navigation -->
<script src="./js/bootstrap.min.js"></script>
<script src="./js/bootstrap3-typeahead.js"></script>
<script src="./js/bootstrap-slider.js"></script>
<script src="./js/raphael-min.js"></script> 
<script src="./js/jsphylosvg.js?t={{time.time()}}"></script>         
<script src="./js/{{js}}.js?={{time.time()}}"></script>
</body> 
</html>
