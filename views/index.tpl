% rebase('base.tpl', js='index')
<!-- The fileinput-button span is used to style the file input field as button -->
<h4>1. Choose Profile HMMs</h4>
<div class="row">
  <div class="col-md-5" id="available-hmms">
    <span>a) Loading list of available HMMs and pathways. Please wait...</span>
    <br/><br/>
  </div>
  <div class="col-md-7">
    <span>b) and/or upload your own HMM files:</span>
    <br/><br/>
    <span class="btn btn-success fileinput-button">
        <i class="glyphicon glyphicon-plus"></i>
        <span>Upload file(s)...</span>
        <!-- The file input field used as target for the file upload widget -->
        <input id="hmm-upload" type="file" name="files[]" multiple>
    </span>
    <br>
    <br>
    <!-- The global progress bar -->
    <div id="hmm-upload-progress" class="progress">
        <div class="progress-bar progress-bar-success"></div>
    </div>
    <!-- The container for the uploaded files -->
  </div>
  <div class="col-md-offset-5 col-md-7">
    <span>
      c) and/or select the default set of profile HMMs for taxonomic profiling:
    </span>
    <br/><br/>
    <button id="markers" class="btn btn-md btn-success">
      Select Taxonomic Markers
    </button>
  </div>
  <div class="col-md-12">
    <div id="hmm-upload-files" class="files"></div>
  </div>
</div>
<hr/>
<h4>2. Choose Metagenome ORF Files</h4>
<div class="row">
  <div class="col-md-5" id="available-orfs">
    <span>a) Loading list of available ORF files. Please wait...</span>
    <br/><br/>
  </div>
  <div class="col-md-7">
    <span>b) and/or upload your own protein FASTA files:</span>
    <br/><br/>
    <!-- The fileinput-button span is used to style the file input field as button -->
    <span class="btn btn-success fileinput-button">
        <i class="glyphicon glyphicon-plus"></i>
        <span>Upload file(s)...</span>
        <!-- The file input field used as target for the file upload widget -->
        <input id="orf-upload" type="file" name="files[]" multiple>
    </span>
    <br>
    <br>
    <!-- The global progress bar -->
    <div id="orf-upload-progress" class="progress">
        <div class="progress-bar progress-bar-success"></div>
    </div>
  </div>
  <!-- The container for the uploaded files -->
  <div class="col-md-12">
    <div id="orf-upload-files" class="files"></div>
  </div>
</div>
<hr/>
<h4>3. Customize &amp; Submit</h4>
<form class="form-horizontal" id='searchform' role="form">
  <div class="form-group">
    <div class="col-md-12">
      <div class="input-group">
        <div class="input-group-addon">
          <label for="hmm-evalue" style="margin-bottom:0">
            Metagenome HMM E-value cutoff
          </label>
        </div>
        <input type="text" class="form-control" id="hmm-evalue"
               placeholder="1e-3">
      </div>
    </div><br/><br/>
    <div class="col-md-12">
      <div class="input-group">
        <div class="input-group-addon">
          <label for="refseq-hmm-evalue" style="margin-bottom:0">
            RefSeq HMM E-value cutoff
          </label>
        </div>
        <input type="text" class="form-control" id="refseq-hmm-evalue"
               placeholder="1e-6">
      </div>
    </div><br/><br/>
    <div class="col-md-12">
      <div class="input-group">
        <div class="input-group-addon">
          <label for="percent-id" style="margin-bottom:0">
            usearch %ID cutoff
          </label>
        </div>
        <input type="text" class="form-control" id="percent-id"
               placeholder="0.5">
      </div>
    </div><br/><br/><br/>
    <div class="col-md-12">
      <span>Select a method for taxonomic classification:</span>
      <div class="radio">
        <label>
          <input type="radio" name="mode" value="sequence" checked="checked">
          Sequence similarity approach: USEARCH (fast)
        </label>
      </div>
      <div class="radio">
        <label>
          <input type="radio" name="mode" value="phylogenetic">
          Phylogenetic approach: FastTree and pplacer
        </label>
      </div>
      <div class="radio">
        <label>
          <input type="radio" name="mode" value="both">
          Show results for both approaches
        </label>
      </div>
    </div><br/><br/>
  </div>
  <div class="form-group">
    <div class="panel-group col-md-12" id="advanced-accordion">
      <div class="panel panel-default">
        <div class="panel-heading">
          <h4 class="panel-title">
            <a data-toggle="collapse" data-parent="#accordion"
               href="#advanced">
              Advanced Options
            </a>
          </h4>
        </div>
        <div id="advanced" class="panel-collapse">
          <div class="panel-body">
            <div class="checkbox">
              <label>
                <input id="multi-orf" type="checkbox">
                Filter ORFS/reads with multiple HMM hits.
              </label>
            </div>
            <div class="checkbox">
              <label>
                <input id="multi-refseq" type="checkbox">
                Filter Refseq proteins with multiple HMM hits.
              </label>
            </div>
            <div class="checkbox">
              <label>
                <input id="transeq" type="checkbox">
                DNA input. Run EMBOSS <strong>Transeq</strong> on uploaded
                reads.
              </label>
            </div>
            <br/>
            <span>Minimum HMM coverage for RefSeq hits</span>:
            &nbsp;&nbsp;&nbsp;
            <input type="text" id="min-coverage-slider" class="col-lg-12"
                   value="" data-slider-min="0" data-slider-max="1"
                   data-slider-step=".01" data-slider-orientation="horizontal"
                   data-slider-selection="after">
            <br/>
            <span>Minimum HMM alignment length for metagenome hits</span>:
            &nbsp;&nbsp;&nbsp;
            <input type="text" id="min-alignment-slider" class="col-lg-12"
                   value="" data-slider-min="0" data-slider-max="1000"
                   data-slider-step="1" data-slider-orientation="horizontal"
                   data-slider-selection="after">
            <br/><hr/>
            <p>
            To save time, you have the option of uploading a previously
            computed reference alignment, tree, and FastTree log file. These
            files are made available after each analysis for the purpose of
            being re-used. When uploading all 3 of these files, the Refseq
            hmmsearch step and the FastTree step can and will be skipped to
            avoid recomputation of the same results. Note that all 3 files must
            be supplied to use this feature.
            </p><br/>
            <span>Upload Previously Computed Reference MSA:</span>
            <br/><br/>
            <span class="btn btn-success fileinput-button">
                <i class="glyphicon glyphicon-plus"></i>
                <span>Upload file(s)...</span>
                <!-- The file input field used as target for the file upload widget -->
                <input id="msa-upload" type="file" name="files[]" multiple>
            </span>
            <br>
            <br>
            <!-- The global progress bar -->
            <div id="msa-upload-progress" class="progress">
                <div class="progress-bar progress-bar-success"></div>
            </div>
            <!-- The container for the uploaded files -->
            <div id="msa-upload-files" class="files"></div>
            <br/>
            <span>Upload Previously Computed Reference Tree:</span>
            <br/><br/>
            <span class="btn btn-success fileinput-button">
                <i class="glyphicon glyphicon-plus"></i>
                <span>Upload file(s)...</span>
                <!-- The file input field used as target for the file upload widget -->
                <input id="tree-upload" type="file" name="files[]" multiple>
            </span>
            <br>
            <br>
            <!-- The global progress bar -->
            <div id="tree-upload-progress" class="progress">
                <div class="progress-bar progress-bar-success"></div>
            </div>
            <!-- The container for the uploaded files -->
            <div id="tree-upload-files" class="files"></div>
            <br/>
            <span>Upload Previously Computed FastTree Log for Reference Tree:</span>
            <br/><br/>
            <span class="btn btn-success fileinput-button">
                <i class="glyphicon glyphicon-plus"></i>
                <span>Upload file(s)...</span>
                <!-- The file input field used as target for the file upload widget -->
                <input id="log-upload" type="file" name="files[]" multiple>
            </span>
            <br>
            <br>
            <!-- The global progress bar -->
            <div id="log-upload-progress" class="progress">
                <div class="progress-bar progress-bar-success"></div>
            </div>
            <!-- The container for the uploaded files -->
            <div id="log-upload-files" class="files"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="form-group">
    <div class="col-md-12" style="text-align: right">
      <button type="submit" class="btn btn-lg btn-success">Submit</button>
    </div>
  </div>
</form>
<div class="modal fade" id="bad-upload-modal" tabindex="-1" role="dialog"
     aria-labelledby="badUpload" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">File(s) not uploaded.</h4>
      </div>
      <div class="modal-body">
        Please make sure you are uploading HMM files that are recognized by
        HMMER and metagenome/ORF files that are in proper FASTA format.
      </div>
    </div>
  </div>
</div>
<div class="modal fade" id="error-modal" tabindex="-1" role="dialog"
     aria-labelledby="uploadError" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">Job not submitted.</h4>
      </div>
      <div class="modal-body">
        An error occured. Perhaps you are not connect to the internet? Please
        contact us if the problem persists.
      </div>
    </div>
  </div>
</div>
<div class="modal fade" id="no-files-modal" tabindex="-1" role="dialog"
     aria-labelledby="noFiles" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">Missing HMM/ORF file.</h4>
      </div>
      <div class="modal-body">
        Please provide at least 1 HMM file and 1 ORF file.
      </div>
    </div>
  </div>
</div>
