var hmm_files = [];
var orf_files = [];
var msa_files = [];
var tree_files = [];
var log_files = [];
var files = {};
files['hmm-upload'] = hmm_files;
files['orf-upload'] = orf_files;
files['msa-upload'] = msa_files;
files['tree-upload'] = tree_files;
files['log-upload'] = log_files;
var directory_index = {};
var suggestions = {};
var all_hmms = {};
var markers = [];

function PrepareUploader(id) {
  $('#'+id).fileupload({
    url: './'+id+'/',
    dataType: 'json',
    submit: function(e, data) {
      var id = $(this).attr('id');
      $('<p class="'+id+'-wait">Uploading/Verifying...</p>')
          .appendTo('#'+id+'-files');
    },
    done: function (e, data) {
      if (data.result.files.length == 0) {
        $('#bad-upload-modal').modal('show');
      }
      var id = $(this).attr('id');
      $.each(data.result.files, function (index, file) {
        var deleteButton = $('<a target="_blank" href="#remove-' +
          file.key + '" class="btn btn-success btn-xs">remove</a>');
        var p = $('<p id="'+file.key+'"/>');
        p.text(file.name);
        p.append(' ');
        p.append(deleteButton);
        deleteButton.click(Delete);
        p.appendTo('#'+id+'-files');
        files[id].push([file.name, file.key]);
      });
      var bar = $('#'+id+'-progress .progress-bar');
      bar.addClass('notransition');
      bar.css('width', '0%');
      bar[0].offsetHeight;
      bar.removeClass('notransition');
      $('.'+id+'-wait').remove();
    },
    progressall: function (e, data) {
      var id = $(this).attr('id');
      var progress = parseInt(data.loaded / data.total * 100, 10);
      $('#'+id+'-progress .progress-bar').css(
        'width',
        progress + '%'
      );
    }
  });
}

function AggregateFiles(to_aggregate) {
  var aggregated = [];
  for (var i = 0; i < to_aggregate.length; i += 1) {
    aggregated.push(to_aggregate[i].join('||'));
  }
  return aggregated.join(',');
}

$(function () {
    'use strict';
    $.fn.slider.defaults.value = 0;
    $('#min-coverage-slider').slider({formater: function(val) {
      return 100 * Math.round(val * 10000) / 10000 + '%'; 
    }});
    $('#min-alignment-slider').slider();
    $('#advanced').addClass('collapse');
    // Change this to the location of your server-side upload handler:
    PrepareUploader('hmm-upload');
    PrepareUploader('orf-upload');
    PrepareUploader('msa-upload');
    PrepareUploader('tree-upload');
    PrepareUploader('log-upload');

    $('#markers').click(function(e) {
      AddSuggestionsForLabel('taxonomic markers');
    });

    $('#searchform').submit(function(e){
      e.preventDefault();
      if (hmm_files.length == 0 || orf_files.length == 0) {
        $('#no-files-modal').modal('show')
        return;
      }
      var hmm_evalue = parseFloat($('#hmm-evalue').val()) || 1e-3;
      var refseq_hmm_evalue = parseFloat($('#refseq-hmm-evalue').val()) || 1e-6;
      var percent_id = parseFloat($('#percent-id').val()) || 0.5;
      var min_coverage = $('#min-coverage-slider').data('value') || 0.0;
      var min_alignment = $('#min-alignment-slider').data('value') || 0;
      $('#searchform button').attr('disabled','disabled');
      $.post('./submit/', {
        hmm_evalue: hmm_evalue,
        refseq_hmm_evalue: refseq_hmm_evalue,
        percent_id: percent_id,
        min_coverage: min_coverage,
        min_alignment: min_alignment,
        filter_multi_orf: $('#multi-orf').is(':checked') ? '1' : '',
        filter_multi_refseq: $('#multi-refseq').is(':checked') ? '1' : '',
        mode: $("input[name=mode]:checked").val(),
        transeq: $('#transeq').is(':checked') ? '1' : '',
        force_msa: $('#force-msa').is(':checked') ? '1' : '',
        reference_msa: msa_files.length > 0? msa_files[0][1] : '',
        reference_tree: tree_files.length > 0? tree_files[0][1] : '',
        reference_log: log_files.length > 0? log_files[0][1] : '',
        hmm_files: AggregateFiles(hmm_files),
        orf_files: AggregateFiles(orf_files)
      }).done(function(data) {
        window.location.href = './status/' + data['job-id'];
      }).fail(function(data) {
        $('#searchform button').removeAttr('disabled');
        $('#error-modal').modal('show');
      });
    });

    $.get('./hmm_index', function(data) {
      var div = $('#available-hmms');
      div.empty();
      div.append('<span>a) Available HMMs and Pathways. Enter a PFAM/TIGRFAM/'+
                 'Genome property accession, GO id, or keyword.</span><br/><br/>');
      div.append('<div id="hmm-search"><input type="text" class="typeahead" '+
                 'placeholder="Start typing for suggestions..."/></div>'+
                 '<span id="hmm-search-status"></span><br/><br/>');
      markers = data['markers'];
      var properties = data['properties'];
      var prop_to_hmms = data['prop_to_hmms'];
      all_hmms = data['all_hmms'];
      var go_props = data['go_props'];
      PrepareSuggestions(properties, prop_to_hmms, go_props);
      var typeahead = $('#hmm-search .typeahead');
      typeahead.typeahead({source: Object.keys(suggestions), items:'all',
                           minLength: 3});
      typeahead.change(SelectedSuggestion);
      $('#hmm-search-status').css('color', 'green');
    });
    $.get("./metagenomes/", function( data ) {
      var div = $('#available-orfs');
      div.empty();
      div.append('<span>a) Available ORF files:</span><br/><br/>');
      var menu = $('<ul>');
      div.append(menu);
      div.append('<br/>');
      MetagenomesList(data['listing'], menu, 'stored/');
      menu.menu({
        select: function(event, ui) {
          var path = ui.item.attr('id');
          if (path.indexOf('all-') == 0) {
            path = path.substr(4);
            var path_files = directory_index[path];
            for (var i = 0; i < path_files.length; i += 1) {
              var name = path_files[i].substr(path_files[i].lastIndexOf('/')+1);
              name = name.replace(/_/g,' ');
              var safe_path = path_files[i].replace(/\//g, '---')
                                           .replace(/\./g, '___');
              var deleteButton = $('<a target="_blank" href="#remove-' +
                safe_path + '" class="btn btn-success btn-xs">remove</a>');
              var p = $('<p id="'+safe_path+'"/>');
              p.text(name);
              p.append(' ');
              p.append(deleteButton);
              deleteButton.click(Delete);
              p.appendTo('#orf-upload-files');
              orf_files.push([name, path_files[i]]);
            }
          } else if (path.indexOf('stored') == 0) {
            var name = ui.item.text();
            var safe_path = path.replace(/\//g, '---')
                                .replace(/\./g, '___');
            var deleteButton = $('<a target="_blank" href="#remove-' +
              safe_path + '" class="btn btn-success btn-xs">remove</a>');
            var p = $('<p id="'+safe_path+'"/>');
            p.text(name);
            p.append(' ');
            p.append(deleteButton);
            deleteButton.click(Delete);
            p.appendTo('#orf-upload-files');
            orf_files.push([name, path]);
          }
        }
      });
    });
});

function Delete(e) {
  e.preventDefault();
  var name = $(this).attr('href').substr(8);
  $('#'+name).remove();
  if (name.indexOf('stored') == 0) {
    name = name.replace(/---/g, '/').replace(/___/g, '.');
  } else {
    $.ajax({url: './delete/'+name, type: 'DELETE'});
  }
  for (var k in files) {
    if (files.hasOwnProperty(k)) {
      var search_files = files[k];
      for (var i = 0; i < search_files.length; i += 1) {
        if (search_files[i][1] == name) {
          search_files.splice(i, 1);
        }
      }
    }
  }
}

function MetagenomesList(metagenomes, container, full) {
  var current_files = [];
  for (var i = 0; i < metagenomes.length; i += 1) {
    var li = $('<li>');
    container.append(li);
    if (typeof metagenomes[i] == "string") {
      li.text(metagenomes[i].replace(/_/g,' '));
      li.attr('id',full+metagenomes[i]);
      current_files.push(full+metagenomes[i]);
    } else {
      var ul = $('<ul>');
      li.text(metagenomes[i][0].replace(/_/g,' '));
      li.append(ul);
      ul.attr('id', full+metagenomes[i][0]);
      MetagenomesList(metagenomes[i][1], ul, full+metagenomes[i][0]+'/');
    }
  }
  if (current_files.length > 1) {
    var li = $('<li>Select All</li>');
    li.attr('id', 'all-'+container.attr('id'));
    container.prepend(li);
    directory_index[container.attr('id')] = current_files;
  }
}

function PrepareSuggestions(properties, prop_to_hmms, go_props) {
  suggestions['taxonomic markers'] = markers;
  for (var id in properties){
    if (properties.hasOwnProperty(id)) {
      var val = properties[id];
      var label = val[2] + ': ' + val[0] + ' (' + val[1] + ')';
      suggestions[label] = prop_to_hmms[id];
    }
  }
  for (var id in go_props){
    if (go_props.hasOwnProperty(id)) {
      var val = go_props[id];
      var hmms = [];
      for (var i = 0; i < val.length; i += 1) {
        hmms = hmms.concat(prop_to_hmms[val[i]]);
      }
      suggestions[id] = hmms;
    }
  }
  for (var id in all_hmms){
    if (all_hmms.hasOwnProperty(id)) {
      var val = all_hmms[id];
      var label = id + ': ' + val;
      suggestions[label] = [id];
    }
  }
}

function SelectedSuggestion(e) {
  var label = $(this).val();
  if (!(label in suggestions)) {
    return;
  }
  AddSuggestionsForLabel(label);;
  $(this).val('');
}

function AddSuggestionsForLabel(label) {
  var hmms = suggestions[label];
  $('#hmm-search-status').text('Selected ' + label + '. Added ' + hmms.length +
                               ' HMM profiles.');
  for (var i = 0; i < hmms.length; i += 1) {
    var hmm = hmms[i];
    var deleteButton = $('<a target="_blank" href="#remove-stored-' + hmm +
                         '" class="btn btn-success btn-xs">remove</a>');
    var p = $('<p id="stored-'+hmm+'"/>');
    p.text(hmm + ': '+all_hmms[hmm]);
    p.append('&nbsp;&nbsp;&nbsp;');
    p.append(deleteButton);
    deleteButton.click(Delete);
    p.appendTo('#hmm-upload-files');
    hmm_files.push([hmm, 'stored-'+hmm]);
  }
}
