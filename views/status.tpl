% rebase('base.tpl', js='status')
<h5>Status for job <span style="color:green">{{job}}</span>:</h5>
<p>Feel free to bookmark this job. You can close and re-open this page at
   anytime during or after execution. After execution, the job data will be
   available for at most 31 days.
 </p>
<p id="status">Loading...</p>
<div id="results"></div>

<div class="modal fade" id="tree-modal" tabindex="-1" role="dialog"
     aria-labelledby="Subtree" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">Subtree</h4>
        <span style="color:#FF0000; font-weight:bold">Red</span>:
        Target ORF/Read<br/>
        <span style="color:#0000FF; font-weight:bold">Blue</span>:
        Closest RefSeq Protein<br/>
        <span style="color:#9999FF; font-weight:bold">Light Blue</span>:
        Other RefSeq Proteins<br/>
      </div>
      <div class="modal-body">
        <div id="tree-svg" style="overflow-x:scroll"> </div>
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="compare-modal" tabindex="-1" role="dialog"
     aria-labelledby="CompareChart" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">Compare Taxonomic Abundance</h4>
      </div>
      <div class="modal-body">
        <div id="compare-settings">
        </div>
        <div id="compare-results">
        </div>
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="process-modal" tabindex="-1" role="dialog"
     aria-labelledby="Process" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">STDOUT and STDERR of current process</h4>
      </div>
      <div class="modal-body">
        STDOUT:<br/>
        <div id="stdout">
        </div>
        STDERR:<br/>
        <div id="stderr">
        </div>
        <br/>Problem? Taking too long?
        <button type="button" class="btn btn-danger" id="stop">
          Force Stop
        </button>
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="krona-modal" tabindex="-1" role="dialog"
     aria-labelledby="KronaChart" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">Krona Chart</h4>
      </div>
      <div class="modal-body">
      </div>
    </div>
  </div>
</div>

<div class="modal fade" id="sequence-modal" tabindex="-1" role="dialog"
     aria-labelledby="Sequence" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>
        <h4 class="modal-title">Read/ORF Sequence</h4>
      </div>
      <div class="modal-body">
      </div>
    </div>
  </div>
</div>

<div class="modal" id="pleaseWaitDialog" data-backdrop="static"
     data-keyboard="false" aria-labelledby="Loading" aria-hidden="true">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h4 class="modal-title">Loading</h4>
      </div>
      <div class="modal-body">
        Please wait...
      </div>
    </div>
  </div>
</div>
