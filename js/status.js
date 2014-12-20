var RESULTS_PER_PAGE = 100;
var MAX_PAGING = 10;
var current_page = 0;
var current_paging = 0;
var current_lines = [];
var include_dataset_column = false;
var include_hmm_column = false;
var job_id = null;
var interval = null;
var output_interval = null;
var xhr = null;
var trees = {};
var read_datasets = {};
var include_indexes = {};
var column_indexes = {};
var dataset_index = -1;
var hmm_index = -1;
var orf_index = -1;
var homolog_index = -1;
var headers = [];
var current_sort_column = -1;
var current_sort_up = false;
var only_usearch = false; // historical
var sequence_classification = false;
var phylogenetic_classification = false;
var no_exist_count = 0;
var annotations_url = null;
var compare_annotations = null;
var compairison_data = null;
var current_stderr = null;
var current_stdout = null;
var current_pid = null;

var DEFAULT_COLUMNS = [
  'ORF', 'HMM E-val', 'Aligned Length', 'Closest Homolog',
  'Closest Homolog Species', '%id of Closest Homolog', 'Best Representative',
  'Representative Proportion']

var TAXONOMY_COLUMNS = [
  'Species', 'Genus', 'Family', 'Order', 'Class', 'Phylum', 'Superkingdom'
]

function CleanHmmName(hmm_name) {
  if (hmm_name.indexOf('_') >= 0) {
    return hmm_name.substr(0, hmm_name.lastIndexOf('_'));
  } else {
    return hmm_name;
  }
}

function CleanDatasetName(dataset_name) {
  if (dataset_name.indexOf('_') >= 0) {
    return dataset_name.substr(0, dataset_name.lastIndexOf('_'));
  } else {
    return dataset_name;
  }
}

function MakeParametersBox(parameters) {
  var box = $('<div class="parameters" />');
  box.append('<strong>Parameters used:</strong><br/>');
  for (var i = 0; i < parameters.length; i += 1) {
    var parameter = parameters[i];
    var span = $('<span />');
    if (parameter[1] !== '') {
      span.text(parameter[0] + ': ' + parameter[1]);
    } else {
      span.text(parameter[0]);
    }
    box.append(span);
    box.append('<br/>');
  }
  return box;
}

function refresh() {
  if (xhr && xhr.readystate != 4) {
    xhr.abort();
  }
  xhr = $.get( "./job"+job_id, function( data ) {
    if (!jQuery.isEmptyObject(data)) {
      if ('no_exist' in data) {
        if (no_exist_count >= 1) {
          $('#status').empty().append('Job does not exists.');
          clearInterval(interval);
        } else {
          no_exist_count += 1;
        }
        return;
      }
      var status_box = $('#status');
      status_box.empty();
      if ('failed' in data) {
        status_box.append('Job terminated before completion.');
        clearInterval(interval);
        return;
      }
      var parameters = null;
      if ('meta' in data && 'parameters' in data['meta']) {
        parameters = data['meta']['parameters'];
      } else if ('result' in data && 'parameters' in data['result']) {
        parameters = data['result']['parameters'];
      }
      if (parameters) {
        status_box.append(MakeParametersBox(parameters));
        status_box.append('<br/>');
      }

      if ('meta' in data) {
        var num_orfs = -1;
        var num_refs = -1;
        var meta = data['meta'];
        current_pid = 'pid' in meta ? meta['pid'] : null;
        current_stdout = 'stdout' in meta ? meta['stdout'] : null;
        current_stderr = 'stderr' in meta ? meta['stderr'] : null;
        if ('analysis' in meta && 'sub-analyses' in meta) {
          status_box.append($('<span/>').text(
              'Analysis #' + meta['analysis'] + ' of ' +meta['sub-analyses']+
              ': '));
          if ('hmm' in meta) {
            status_box.append($('<span/>').text(CleanHmmName(meta['hmm'])));
          }
          status_box.append('<br/>');
        }
        if ('total_orfs' in meta) {
          num_orfs = meta['total_orfs'];
        }
        if ('total_refs' in meta) {
          num_refs = meta['total_refs'];
        }
        status_box.append('<br/>');
      }

      if ('position' in data) {
        var position = data['position'];
        status_box.append($('<strong/>').text('Queued: (' + position[0] +
                                              ' of ' + position[1] +')'));
        status_box.append('<br/>');
        status_box.append('<a href="./unsubmit/'+job_id+'">Cancel Job</a>');
      }
      if ('state' in data) {
        var state = data['state'];
        var states = data['states'];
        var reached_current = false;
        for (var i = 0; i < states.length; i += 1) {
          var description = states[i][1];
          var is_current = states[i][0] == state;
          reached_current = reached_current || is_current;
          if (!reached_current) {
            var checkmark = $('<span style="color:green">&#x2713; </span>');
            status_box.append(checkmark);
            status_box.append(description);
            if (states[i][0] == 'HMMSEARCH1' && num_orfs >= 0) {
              status_box.append(' - matched <strong>~' + num_orfs +
                                ' reads</strong>');
            } else if (states[i][0] == 'HMMSEARCH2' && num_refs >= 0) {
              status_box.append(' - matched <strong>~' + num_refs +
                                ' RefSeq proteins</strong>');
            }
          } else if (is_current) {
            status_box.append('<strong>' + description + '</strong>');
          } else {
            var span = $('<span style="color:#DDDDDD" />');
            span.text(description);
            status_box.append(span);
          }
          status_box.append('<br/>');
        }
        status_box.append('<br/>');
        if (current_stdout && current_stderr && current_pid) {
          var view_output = $('<button type="button" class="btn btn-warning">'+
                              'View STDOUT/STDERR</button>');
          view_output.click(ViewOutput);
          status_box.append(view_output);
          status_box.append('<br/><br/>');
        }
      }

      if ('result' in data) {
        clearInterval(interval);
        status_box.append('<strong>Downloads and Visualizations</strong>'+
                          '<br/><br/>');
        var compare = $('<button type="button" class="btn btn-default">'+
                        '<span class="glyphicon glyphicon-list-alt"></span> '+
                        'Compare Taxonomic Abundance</button>');
        compare.click(PrepareCompareSettings);
        status_box.append(compare);
        status_box.append('<br/><br/>');
        status_box.append(CreateSummary(data['result']));
      }
      // Bug on chrome: border not render correctly after inserting new
      // elements.
      $('.myborder').toggle().toggle();
    }
  });
}

function ViewOutput() {
  if (output_interval != null) {
    clearInterval(output_interval);
  }
  output_interval = setInterval(RefreshProcessOutput, 2000);
  $('#process-modal').modal('show');
}

function PrepareCompareSettings() {
  $.get('./annotations/'+annotations_url, CreateCompareSettings);
}

function CreateCompareSettings(data) {
  compare_annotations = data;
  var datasets = {};
  var hmms = {};
  var lines = compare_annotations.split('\n');
  for (var i = 1; i < lines.length - 1; i += 1) {
    var parts = lines[i].split('\t');
    datasets[parts[0]] = true;
    hmms[parts[1]] = true;
  }
  var compare = $('#compare-settings');
  compare.empty();
  $('#compare-results').empty().hide();
  // Datasets
  var dataset_checkboxes = $('<div class="panel-body"/>');
  for (var dataset in datasets) {
    if (!datasets.hasOwnProperty(dataset)) {
      continue;
    }
    var checkbox = $('<div class="checkbox">'+
                       '<label>'+
                         '<input name="datasets" value="'+dataset+'"'+
                                'type="checkbox" checked="checked"> '+dataset+
                       '</label>'+
                     '</div>');
    dataset_checkboxes.append(checkbox);
  }
  compare.append('<strong>Choose datasets to compare:</strong>');
  compare.append(dataset_checkboxes);
  // Hmms
  var hmm_checkboxes = $('<div class="panel-body"/>');
  for (var hmm in hmms) {
    if (!hmms.hasOwnProperty(hmm)) {
      continue;
    }
    var checkbox = $('<div class="checkbox">'+
                       '<label>'+
                         '<input name="hmms" value="'+hmm+'"'+
                                'type="checkbox" checked="checked"> '+hmm+
                       '</label>'+
                     '</div>');
    hmm_checkboxes.append(checkbox);
  }
  compare.append('<strong>Choose HMMs to compare:</strong>');
  compare.append(hmm_checkboxes);
  // Taxonomy.
  var taxonomy_level = $('<div id="taxonomic" class="btn-group-vertical" />');
  var first = true;
  for (var i = 0; i < TAXONOMY_COLUMNS.length; i += 1) {
    var button = $('<button type="button" class="btn btn-default'+
                   (first? ' active':'')+'" />');
    button.text(TAXONOMY_COLUMNS[i]);
    taxonomy_level.append(button);
    first = false;
  }
  compare.append('<strong>Choose taxonomic level to compare:</strong><br/><br/>');
  compare.append(taxonomy_level);
  taxonomy_level.find('button').click(function() {
    $('.btn-group-vertical .btn').removeClass('active');
    $(this).addClass('active');
  });

  var compare_button = $('<button type="button" class="btn btn-primary" />');
  compare_button.text('Generate Compairison Heatmap');
  compare_button.click(GenerateCompare);
  compare.append('<br/><br/>');
  compare.append(compare_button);

  compare.show();
  $('#compare-modal').modal('show');
}

function GenerateCompare() {
  var datasets = $("input[name='datasets']:checked").map(function() {
    return $(this).val();
  }).get();
  var hmms = $("input[name='hmms']:checked").map(function() {
    return $(this).val();
  }).get();
  if (hmms.length == 0 || datasets.length == 0) {
    return;
  }
  var lines = compare_annotations.split('\n');
  var titles = lines[0].split('\t');
  var taxonomy = $('#taxonomic .btn.active').text();
  var taxonomy_indices = {};
  var taxonomy_level = -1;
  for (var i = 0; i < TAXONOMY_COLUMNS.length; i += 1) {
    if (TAXONOMY_COLUMNS[i] == taxonomy) {
      taxonomy_level = i;
    }
    for (var j = 0; j < titles.length; j += 1) {
      if (titles[j].indexOf(' ' + TAXONOMY_COLUMNS[i]) >= 0) {
        taxonomy_indices[TAXONOMY_COLUMNS[i]] = j;
      }
    }
  }
  var all_organisms = {};
  var counts = {};
  for (var i = 0; i < datasets.length; i += 1) {
    var dataset_hmms = {};
    for (var j = 0; j < hmms.length; j += 1) {
      dataset_hmms[hmms[j]] = {'*total*':0};
    }
    counts[datasets[i]] = dataset_hmms;
  }
  for (var i = 1; i < lines.length - 1; i += 1) {
    var parts = lines[i].split('\t');
    var dataset = parts[0];
    var hmm = parts[1];
    if (!counts.hasOwnProperty(dataset) ||
        !counts[dataset].hasOwnProperty(hmm)) {
      continue;
    }
    // Finds best annotation.
    var organism = 'unclassified';
    for (var j = taxonomy_level; j < TAXONOMY_COLUMNS.length; j += 1) {
      var current_taxonomy = TAXONOMY_COLUMNS[taxonomy_level];
      if (!taxonomy_indices.hasOwnProperty(current_taxonomy)) {
        continue;
      }
      var level_index = taxonomy_indices[current_taxonomy];
      var current_annotation = parts[level_index];
      if ((current_annotation == 'unclassified' || current_annotation == '') &&
          j < TAXONOMY_COLUMNS.length - 1) {
        var next_taxonomy = TAXONOMY_COLUMNS[j+1];
        var next_level_index = taxonomy_indices[next_taxonomy];
        var next_annotation = parts[next_level_index];
        if (next_annotation != 'unclassified' && next_annotation != '') {
          organism = 'unclassified ' + next_annotation;
          break;
        }
      } else {
        organism = current_annotation;
        break;
      }
    }
    all_organisms[organism] = true;
    var count = counts[dataset][hmm];
    if (organism in count) {
      count[organism] += 1;
    } else {
      count[organism] = 1;
    }
    count['*total*'] += 1;
  }

  var charts = $('#compare-results');
  var download = $('<button type="button" class="btn btn-default">'+
                   '<span class="glyphicon glyphicon-list-alt"></span> '+
                   'Download</button>');
  download.click(DownloadCompareStats);
  charts.append(download);
  charts.append('<br/><br/>');
  var table = $('<table class="compare"/>');
  var title_row = $('<tr/>');
  title_row.append('<th class="first">'+taxonomy+'</th>');
  for (var i = 0; i < datasets.length; i += 1) {
    var dataset = datasets[i];
    for (var j = 0; j < hmms.length; j += 1) {
      title_row.append('<th'+(j==hmms.length - 1?' class="last"':'')+'>'
                       +(j==0? dataset.replace(/_/g, ' ')+
                       '<br/><br/>':'')+
                       CleanHmmName(hmms[j])+'</th>');
    }
  }
  table.append(title_row);
  for (var organism in all_organisms) {
    if (!(all_organisms.hasOwnProperty(organism))) {
      continue;
    }
    var row = $('<tr/>');
    row.append('<td class="first">'+organism+'</td>');
    for (var i = 0; i < datasets.length; i += 1) {
      var dataset = datasets[i];
      for (var j = 0; j < hmms.length; j += 1) {
        var hmm = hmms[j];
        var cell = $('<td'+(j==hmms.length - 1?' class="last"':'')+'/>');
        var column = counts[dataset][hmm];
        if (organism in column) {
          var value = column[organism]/Math.max(column['*total*'], 1);
          var color = Math.round((1-value)*255);
          cell.css('background-color','rgb(255,'+color+','+color+')');
          cell.text(Math.round(value*100)/100);
        } else {
          cell.text('0');
        }
        row.append(cell);
      }
      table.append(row);
    }
    charts.append(table);
  }
  compairison_data = {datasets: datasets, hmms: hmms, counts: counts,
                      organisms: all_organisms, taxonomy: taxonomy};
  $('#compare-settings').hide();
  charts.show();
}

function DownloadCompareStats() {
  var datasets = compairison_data['datasets'];
  var hmms = compairison_data['hmms'];
  var counts = compairison_data['counts'];
  var all_organisms = compairison_data['organisms'];
  var taxonomy = compairison_data['taxonomy'];
  var lines = [];
  var first_line = '';
  var second_line = taxonomy;
  for (var i = 0; i < datasets.length; i += 1) {
    var dataset = datasets[i];
    first_line += '\t' + dataset.replace(/_/g, ' ');
    for (var j = 0; j < hmms.length; j += 1) {
      var hmm = hmms[j];
      if (j > 0) {
        first_line += '\t';
      }
      second_line += '\t'+CleanHmmName(hmm);
    }
  }
  lines.push(first_line + '\n')
  lines.push(second_line + '\n')
  for (var organism in all_organisms) {
    if (!(all_organisms.hasOwnProperty(organism))) {
      continue;
    }
    var line = organism;
    for (var i = 0; i < datasets.length; i += 1) {
      var dataset = datasets[i];
      for (var j = 0; j < hmms.length; j += 1) {
        var hmm = hmms[j];
        var column = counts[dataset][hmm];
        if (organism in column) {
          var value = column[organism]/Math.max(column['*total*'], 1);
          line += '\t' + Math.round(value*100)/100;
        } else {
          line += '\t0.0';
        }
      }
    }
    lines.push(line + '\n');
  }
  var blob = new Blob(lines, {type: "text/plain;charset=utf-8"});
  saveAs(blob, 'taxonomic_comparison.tsv');
}

function CreateSummary(results) {
  if ('only_usearch' in results) {
    only_usearch = results['only_usearch']
  }
  if ('sequence_classification' in results) {
    sequence_classification = results['sequence_classification']
    only_usearch = true;
  }
  if ('phylogenetic_classification' in results) {
    phylogenetic_classification = results['phylogenetic_classification']
    only_usearch = false;
  }

  $('body').on('click', function (e) {
    //did not click a popover toggle or popover
    if ($(e.target).data('toggle') !== 'popover'
        && $(e.target).parents('.popover.in').length === 0) { 
      $('[data-toggle="popover"]').popover('hide');
    }
  });
  var table = $('<table class="summary"/>');
  var sizes = [];
  var total_size = 0;
  for (var r = 0; r < results['rows'].length; r += 1) {
    var row = results['rows'][r];
    var size = row['total_sequences'];
    sizes.push(size);
    total_size += size;
    read_datasets[row['name']] = {};
  }
  for (var r = -1; r <= results['rows'].length; r += 1) {
    var tr = $('<tr/>');
    table.append(tr);
    if (r == -1) {
      tr.append('<th>Datasets</th>');
    } else if (r == results['rows'].length){
      if (results['rows'].length <= 1) {
        break;
      }
      tr.append('<td><strong>All Datasets</strong>'+
                '<br/><br/>Total Reads: '+Commas(total_size)+'</td>');
    } else {
      var row = results['rows'][r];
      tr.append('<td><strong>'+row['name'].replace(/_/g,' ')+
                '</strong><br/><br/>Total Reads: '+
                Commas(row['total_sequences'])+'</td>');
    }
    for (var c = 0; c < results['column_order'].length; c += 1) {
      var column_name = results['column_order'][c];
      var column = results['columns'][column_name];
      var tree_path = null;
      if (r == -1) {
        var th = $('<th/>').text(column_name + ': ' + column['description']);
        tr.append(th);
        th.append('<br/><br/>');
        if (column.hasOwnProperty('tree')) {
          tree_path = column['tree'];
          th.append(MakeTreeButton(tree_path));
          trees[column_name] = tree_path;
        } else {
          trees[column_name] = null;
        }
        if (column.hasOwnProperty('refseq_tree')) {
          th.append(MakeTreeButton(column['refseq_tree'], 'refseq'));
        }
        if (column.hasOwnProperty('refseq_log')) {
          th.append(MakeLogButton(column['refseq_log']));
        }
        if (column.hasOwnProperty('msa')) {
          th.append(MakeMSAButton(column['msa']));
        }
        if (column.hasOwnProperty('refseq_msa')) {
          th.append(MakeMSAButton(column['refseq_msa'], 'refseq'));
        }

      } else if (r == results['rows'].length) {
        var td = $('<td/>');
        tr.append(td);
        // Annotations
        if (column.hasOwnProperty('all_annotations')) {
          if (!results.hasOwnProperty('all_annotations')) {
            annotations_url = column['all_annotations'];
          }
          td.append(MakeDownloadAnnotationsButton(column['all_annotations']));
          td.append(MakeViewAnnotationsButton(column['all_annotations'],
                    column_name, 'all'));
        }
        // Reads
        if (column.hasOwnProperty('all_reads')) {
          td.append(MakeReadsButton(column['all_reads']));
        }
        // Krona charts
        var hmm_krona = null;
        var dataset_krona = null;
        if (column.hasOwnProperty('hmm_krona')) {
          hmm_krona = column['hmm_krona'];
        }
        if (column.hasOwnProperty('dataset_krona')) {
          dataset_krona = column['dataset_krona'];
        }
        td.append(MakeKronaButton(hmm_krona, dataset_krona))
        td.append('<br/>');
        var total = ColumnTotal(column);
        td.append('Reads Matched: ' + Commas(total) + ' ('+
                  Proportion(total, total_size)+ '%)');
      } else {
        var td = $('<td/>');
        tr.append(td);
        var cell = column['rows'][r];
        // Annotations
        if (cell.hasOwnProperty('annotations')) {
          if (annotations_url == null) {
            annotations_url = cell['annotations'];
          }
          td.append(MakeDownloadAnnotationsButton(cell['annotations']));
          td.append(MakeViewAnnotationsButton(cell['annotations'],
                    column_name, results['rows'][r]['name']));
        }
        // Reads
        if (cell.hasOwnProperty('reads_file')) {
          td.append(MakeReadsButton(cell['reads_file']));
          read_datasets[results['rows'][r]['name']][column_name] =
              cell['reads_file'];
        }
        // Krona charts
        var hmm_krona = null;
        var dataset_krona = null;
        if (cell.hasOwnProperty('hmm_krona')) {
          hmm_krona = cell['hmm_krona'];
        }
        if (cell.hasOwnProperty('dataset_krona')) {
          dataset_krona = cell['dataset_krona'];
        }
        td.append(MakeKronaButton(hmm_krona, dataset_krona));
        td.append('<br/>');
        td.append('Reads Matched: ' + Commas(cell['sequences_hit']) + ' ('+
                  Proportion(cell['sequences_hit'], sizes[r])+'%)');
      }
    }
    if (results['column_order'].length > 1) {
      if (r == -1) {
        tr.append('<th>All HMMs</th>');
      } else if (r == results['rows'].length) {
        var td = $('<td/>');
        tr.append(td);
        // Annotations
        if (results.hasOwnProperty('all_annotations')) {
          annotations_url = results['all_annotations'];
          td.append(MakeDownloadAnnotationsButton(results['all_annotations']));
          td.append(MakeViewAnnotationsButton(results['all_annotations'],
                    'all', 'all'));
        }
        // Reads
        if (results.hasOwnProperty('all_reads')) {
          td.append(MakeReadsButton(results['all_reads']));
        }
        // Krona charts
        var hmm_krona = null;
        var dataset_krona = null;
        if (results.hasOwnProperty('hmm_krona')) {
          hmm_krona = results['hmm_krona'];
        }
        if (results.hasOwnProperty('dataset_krona')) {
          dataset_krona = results['dataset_krona'];
        }
        td.append(MakeKronaButton(hmm_krona, dataset_krona));
        var dataset_total = DatasetTotal(results);
        td.append('<br/>');
        td.append('Reads Matched: ' + Commas(dataset_total) + ' ('+
                  Proportion(dataset_total, total_size)
                  + '%)');
      } else {
        var td = $('<td/>');
        tr.append(td);
        // Annotations
        if (row.hasOwnProperty('all_annotations')) {
          if (!results.hasOwnProperty('all_annotations')) {
            annotations_url = row['all_annotations'];
          }
          td.append(MakeDownloadAnnotationsButton(row['all_annotations']));
          td.append(MakeViewAnnotationsButton(row['all_annotations'],
                    'all', results['rows'][r]['name']));
        }
        // Reads
        if (row.hasOwnProperty('all_reads')) {
          td.append(MakeReadsButton(row['all_reads']));
        }
        // Krona charts
        var hmm_krona = null;
        var dataset_krona = null;
        if (row.hasOwnProperty('hmm_krona')) {
          hmm_krona = row['hmm_krona'];
        }
        if (row.hasOwnProperty('dataset_krona')) {
          dataset_krona = row['dataset_krona'];
        }
        td.append(MakeKronaButton(hmm_krona, dataset_krona));
        var row_total = RowTotal(results, r);
        td.append('<br/>');
        td.append('Reads Matched: ' + Commas(row_total) + ' ('+
                  Proportion(row_total, results['rows'][r]['total_sequences'])
                  + '%)');
      }
    }
  }
  var rows = table.find('tr');
  for (var i = 0; i < rows.length; i += 1) {
    var row = $(rows[i]);
    var cols = row.find('td');
    if (cols.length == 0) {
      cols = row.find('th');
    }
    for (var j = 0; j < cols.length; j += 1) {
      var col = $(cols[j]);
      if (j % 2 == 1) {
        col.addClass('g');
      }
    }
  }
  return table;
}

function MakeTreeButton(path, is_refseq) {
  return $('<a target="_blank" href="./tree/'+path+
           '" class="btn btn-default btn-xs">Download '+
           (is_refseq === undefined ? 'Full':'RefSeq')+' Tree</a>');
}

function MakeMSAButton(path, is_refseq) {
  return $('<a target="_blank" href="./alignment/'+path+
           '" class="btn btn-default btn-xs">Download '+
           (is_refseq === undefined ? 'Full':'RefSeq')+' MSA</a>');
}

function MakeLogButton(path) {
  return $('<a target="_blank" href="./fasttree-log/'+path+
           '" class="btn btn-default btn-xs">Download FastTree Log</a>');
}

function MakeReadsButton(path) {
  return $('<a target="_blank" href="./reads/'+path+
           '" class="btn btn-default btn-xs">Download Full Reads</a>');
}

function MakeDownloadAnnotationsButton(path) {
  return $('<a target="_blank" href="./annotations/'+path+
           '" class="btn btn-default btn-xs">Download Annotations</a>')
}

function MakeViewAnnotationsButton(path, hmm, dataset) {
  var view = $('<a href="#view-'+path+'*'+hmm+'*'+dataset+'*" '+
               'class="btn btn-default btn-xs">View Annotations</a>');
  view.click(ViewResults);
  return view;
}

function MakeKronaButton(hmm_path, dataset_path) {
  if (!hmm_path != !dataset_path) { // xor
    var path = hmm_path || dataset_path;
    var view = $('<a data-toggle="tooltip" title="View Krona chart" '+
                 'data-placement="top" href="/krona/'+path+'" '+
                 'class="krona-single"></a>');
    view.tooltip();
    view.click(ShowKrona);
    return view;
  } else if (hmm_path && dataset_path) {
    var trigger = $('<button data-toggle="popover" class="krona-single"/>');
    trigger.popover({
      html : true,
      placement : 'top',
      content : function() {
        var container = $('<span/>');
        var view1 = $('<a data-toggle="tooltip" title="'+
                      'Compare to other datasets" href="/krona/'+hmm_path+
                      '" data-placement="right" class="krona-ud"></a>');
        view1.click(ShowKrona);
        view1.tooltip();
        var view2 = $('<a data-toggle="tooltip" title="Compare to other HMMs" '+
                      'href="/krona/'+dataset_path+
                      '" data-placement="right" class="krona-lr"></a>');
        view2.click(ShowKrona);
        view2.tooltip();
        container.append(view1);
        container.append('<br/>');
        container.append(view2);
        return container;
      }
    });
    trigger.tooltip({
      placement : 'bottom',
      title : 'View krona chart'
    });
    return trigger;
  } else {
    return '<span class="krona-place-holder" />';
  }
}

function Proportion(numerator, denominator) {
  return Math.round(numerator / denominator * 10000000) / 100000
}

function Commas(x) {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function ColumnTotal(column) {
  var total = 0;
  for (var i = 0; i < column['rows'].length; i += 1) {
    var cell = column['rows'][i];
    total += cell['sequences_hit'];
  }
  return total;
}

function RowTotal(results, r) {
  var total = 0;
  for (var i = 0; i < results['column_order'].length; i += 1) {
    var column_name = results['column_order'][i];
    var column = results['columns'][column_name];
    var cell = column['rows'][r];
    total += cell['sequences_hit'];
  }
  return total;
}

function DatasetTotal(results) {
  var total = 0;
  for (var i = 0; i < results['column_order'].length; i += 1) {
    var column_name = results['column_order'][i];
    var column = results['columns'][column_name];
    for (var j = 0; j < column['rows'].length; j += 1) {
      var cell = column['rows'][j];
      total += cell['sequences_hit'];
    }
  }
  return total;
}

function ViewResults(e) {
  e.preventDefault();
  $('#pleaseWaitDialog').modal('show');
  var href = $(this).attr('href');
  var parts = href.split('*');
  var annotations_file = parts[0].substr(6);
  current_hmm = parts[1];
  current_orfs = parts[2];
  include_dataset_column = current_orfs == 'all';
  include_hmm_column = current_hmm == 'all';
  current_orfs = current_orfs == 'all' ? 'All Datasets' : current_orfs;
  current_hmm = current_hmm == 'all' ? 'All HMMs' : current_hmm;
  $.get('./annotations/'+annotations_file, InitialResults);
}

function Navigate(e) {
  e.preventDefault();
  var href = $(this).attr('href');
  var page = href.substr(1);
  if (page == 'b') {
    current_paging -= MAX_PAGING;
    UpdateNavigation();
  } else if (page =='f') {
    current_paging += MAX_PAGING;
    UpdateNavigation();
  } else {
    current_page = parseInt(page) - 1;
    current_paging = Math.floor(current_page - current_page % MAX_PAGING);
    UpdateNavigation();
    UpdatePage();
  }
}

function UpdateNavigation() {
  var pagination = $('#pagination');
  pagination.empty();
  var num_pages = Math.ceil((current_lines.length-1)/RESULTS_PER_PAGE);
  if (num_pages == 1) {
    return;
  }
  if (current_page != 0) {
    pagination.append('<li><a href="#'+(current_page)+'">&laquo;</a></li>');
  }
  if (current_paging > 0) {
    pagination.append('<li><a href="#b">...</a></li>');
  }
  for (i = current_paging; i < current_paging + MAX_PAGING && i < num_pages;
       i += 1) {
    if (current_page == i) {
      pagination.append('<li class="active"><a href="#'+(i+1)+'">'+(i+1)+
                                           '</a></li>');
    } else {
      pagination.append('<li><a href="#'+(i+1)+'">'+(i+1)+'</a></li>');
    }
  }
  if (current_paging + MAX_PAGING < num_pages) {
    pagination.append('<li><a href="#f">...</a></li>');
  }
  if (current_page != num_pages - 1) {
    pagination.append('<li><a href="#'+(current_page+2)+'">&raquo;</a></li>');
  }
  pagination.find('a').click(Navigate);
}

function SortColumn() {
  var column = parseInt($(this).attr('id').substr(5));
  var is_sorted_down = $(this).hasClass('sort-down');

  $('.col-sort').removeClass('sort-down').removeClass('sort-up');
  current_sort_column = column;
  if (is_sorted_down) {
    current_sort_up = true;
    $(this).addClass('sort-up');
  } else {
    current_sort_up = false;
    $(this).addClass('sort-down');
  }
  $('#pleaseWaitDialog').modal('show');
  setTimeout(function(){
    SortCurrentLines();
    $('#pleaseWaitDialog').modal('hide');
  },500);
}

function isNumeric(n) {
  return !isNaN(parseFloat(n)) && isFinite(n);
}

function SortCurrentLines() {
  current_lines.sort(function(a, b) {
    var columns_a = a.split('\t');
    var columns_b = b.split('\t');
    var value_a = columns_a[current_sort_column];
    var value_b = columns_b[current_sort_column];
    if (isNumeric(value_a) && isNumeric(value_b)) {
      value_a = parseFloat(value_a);
      value_b = parseFloat(value_b);
    }
    if (value_a == value_b) {
      return 0;
    }
    if (value_a > value_b) {
      return current_sort_up ? 1 : -1;
    }
    return current_sort_up ? -1 : 1;
  });
  UpdatePage('no scroll');
}

function UpdatePage(dont_scroll) {
  var table = $('#listing');
  table.empty();
  var start = current_page * RESULTS_PER_PAGE;
  var end = (current_page + 1) * RESULTS_PER_PAGE;

  var header_row = $('<tr />');
  table.append(header_row);
  var even = true;
  for (var i = 0; i < headers.length; i += 1) {
    if (include_columns.hasOwnProperty(i)) {
      var header = headers[i];
      var header_col = $('<th class="listing-header"/>');
      if (even) {
        header_col.addClass('d');
      }
      even = !even;
      var sort_button = $('<button class="col-sort" id="sort-'+i+'"/>');
      if (current_sort_column == i) {
        sort_button.addClass(current_sort_up? 'sort-up':'sort-down');
      }
      header_col.append('<span>'+header+'</span>');
      header_col.append(sort_button);
      sort_button.click(SortColumn);
      header_row.append(header_col);
    }
  }

  for (var i = start; i < Math.min(end, current_lines.length); i += 1) {
    var line = current_lines[i];
    var parts = line.split('\t');
    var row = $('<tr />');
    even = true;
    table.append(row);
    for (var j = 0; j < parts.length; j += 1) {
      if (!(include_columns.hasOwnProperty(j))) {
        continue;
      }
      var col = $('<td />');
      if (even) {
        col.addClass('d');
      }
      if (j == orf_index) {
        var read = parts[j].replace(/_/g, ' ');
        var full_orf = parts[j].substr(0, parts[j].indexOf('_ma'))
        var current_dataset = parts[dataset_index];
        var current_hmm = parts[hmm_index];
        var reads_file = read_datasets[current_dataset][current_hmm];
        var link = $('<a href="/sequence/'+reads_file+'/'+full_orf+'" />');
        link.click(RetrieveSequence);
        link.text(read);
        col.append(link);
      } else if (j == homolog_index && parts[j].indexOf('gi|') >= 0) {
        var gi_num = parts[j].match(/gi\|(\d+)\|/)[1];
        var link = $('<a href="http://www.ncbi.nlm.nih.gov/protein/'+gi_num+
                     '" target="_blank">' + gi_num+'</a>');
        col.append(link);
        if (phylogenetic_classification || !only_usearch) {
          var current_hmm = parts[hmm_index];
          var current_tree = trees[current_hmm];
          if (current_tree) {
            var subtree = $('<a href="#view-'+current_tree+'***'+
                            parts[orf_index]+ '***'+ gi_num +
                            '" class="btn btn-primary btn-xs">subtree</a>');
            subtree.click(ShowSubtree);
            col.append(' ').append(subtree);
          }
        }
      } else {
        col.text(parts[j]);
      }
      even = !even;
      row.append(col);
    }
  }
  if (dont_scroll === undefined) {
    $('html, body').stop(true).animate({
      scrollTop: $('#res-header').offset().top
    }, 500);
  }
}

function RetrieveSequence(e) {
  e.preventDefault();
  $.get($(this).attr('href'), function(data) {
    var modal_popup = $('#sequence-modal');
    var body = modal_popup.find('.modal-body');
    body.empty();
    body.append($('<pre/>').html(data));
    modal_popup.modal('show');
  });
}

function InitialResults(data) {
  current_lines = data.split('\n');
  current_lines.pop();
  var results = $('#results');
  results.empty();
  var column_controller = $(
    '<br/><div class="panel-group" id="advanced-accordion">' +
      '<div class="panel panel-default">' +
        '<div class="panel-heading">' +
          '<h4 class="panel-title">' +
            '<a data-toggle="collapse" data-parent="#accordion" '+
               'href="#columns">' +
              'Manage Columns' +
            '</a>' +
          '</h4>' +
        '</div>' +
        '<div id="columns" class="col-md-12 panel-collapse collapse">' +
        '</div>' +
      '</div>' +
    '</div>');
  results.append(column_controller);
  var h3 = $('<h3 id="res-header">Results for '+CleanDatasetName(current_orfs)+
             (current_orfs == 'all' ? 's':'')+', using '+
             CleanHmmName(current_hmm)+'</h3>');
  results.append(h3);
  var pagination = $('<ul class="pagination" id="pagination"/>');
  results.append(pagination);
  var table = $('<table id="listing"/>');
  results.append(table);
  current_page = 0;
  paging_start = 0;
  UpdateNavigation();

  // Determine which columns to ignore, and find important columns.
  headers = current_lines[0].split('\t');
  current_lines.shift();
  dataset_index = headers.indexOf('Dataset');
  hmm_index = headers.indexOf('HMM Family');
  orf_index = headers.indexOf('ORF');
  homolog_index = headers.indexOf('Closest Homolog');
  column_indexes = {};
  for (var i = 0; i < headers.length; i += 1) {
    column_indexes[headers[i]] = i;
  }
  include_columns = {}
  for (var c = 0; c < DEFAULT_COLUMNS.length; c += 1) {
    var column = DEFAULT_COLUMNS[c];
    if (column_indexes.hasOwnProperty(column)) {
      include_columns[column_indexes[column]] = true;
    }
  }
  if (include_dataset_column) {
    include_columns[dataset_index] = true;
  }
  if (include_hmm_column) {
    include_columns[hmm_index] = true;
  }
  InitializeColumns();
  UpdatePage();
  $('#pleaseWaitDialog').modal('hide');
}

function InitializeColumns() {
  var columns = $('#columns');
  for (var i = 0; i < headers.length; i += 1) {
    var header = headers[i];
    var col_index = column_indexes[header];
    var checkbox = $('<div class="checkbox"><label><input type="checkbox" '+
                     'value="'+col_index+'" '+
                     (include_columns.hasOwnProperty(col_index) ?
                      'checked="checked" ':'') + '/>' + header +
                     '</label></div>');
    columns.append(checkbox);
  }
  $('#columns input').change(function() {
    var value = parseInt($(this).val());
    if ($(this).is(':checked')) {
      include_columns[value] = true;
    } else if (include_columns.hasOwnProperty(value)) {
      delete include_columns[value];
    }
    UpdatePage('No Scroll');
  });

}

function ShowSubtree(e) {
  e.preventDefault();
  var href = $(this).attr('href');
  var parts = href.split('***');
  var current_tree = parts[0].substr(6);
  var node = parts[1];
  var homolog = parts[2];
  $('#tree-svg').empty();
  $('#tree-svg').text('Loading subtree, please wait...');
  $('#tree-modal .modal-title').text('Subtree containing \'' + node+ '\'');
  $('#tree-modal').modal('show');
  $.post('./subtree/', {node:node, homolog:homolog, tree: current_tree},
                       SubtreeReady);
}

function ShowKrona(e) {
  e.preventDefault();
  $('[data-toggle="popover"]').popover('hide');
  var href = $(this).attr('href');
  var krona_modal = $('#krona-modal');
  var container = krona_modal.find('.modal-body');
  container.empty();
  var iframe = $('<iframe />');
  iframe.attr('src', href);
  container.append(iframe);
  krona_modal.modal('show');
}

function SubtreeReady(data) {
  var height = data.match(/<\/ns0:name>/g).length * 15;
  $('#tree-svg').empty();
  phylocanvas = new Smits.PhyloCanvas({phyloxml: data}, 'tree-svg', 800,
                                      height);
  $('#tree-svg svg').attr('width', 20 + svgMaxWidth);
}

function RefreshProcessOutput() {
  if (current_stderr == null || current_stdout == null ||
      !$('#process-modal').is(':visible')) {
    if (output_interval) {
      clearInterval(output_interval);
      output_interval = null;
    }
    return;
  }
  $.post('./tail/', {stdout:current_stdout, stderr:current_stderr}, TailReady);
}

function TailReady(data) {
  var new_content = false;
  if ('stderr' in data) {
    $('#stderr').empty().append($('<pre />').html(data['stderr']));
    new_content = true;
  }
  if ('stdout' in data) {
    $('#stdout').empty().append($('<pre />').html(data['stdout']));
    new_content = true;
  }
  if (!new_content) {
    $('#process-modal').modal('hide');
  }
}

function StopProcess() {
  if (current_pid == null) {
    return;
  }
  $.post('./stop/', {pid:current_pid});
  $('#process-modal').modal('hide');
}

$(function () {
    'use strict';
    job_id = document.URL.substr(document.URL.lastIndexOf('/'));
    refresh();
    interval = setInterval(refresh, 7000);
    $('#stop').click(StopProcess);
    $('#krona-modal').on('shown.bs.modal', function () {
      $('#krona-modal .modal-body').css('height', $(window).height() * 0.8);
    });
});
