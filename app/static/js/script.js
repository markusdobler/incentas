(function() {
  $('.input-group.datepicker').datepicker({
    format: "yyyy-mm-dd",
  weekStart: 1,
  autoclose: true,
  todayHighlight: true
  });
  $('.datepicker-button').datepicker({
    format: "yyyy-mm-dd",
    weekStart: 1,
    autoclose: true,
    todayHighlight: true
  })
  .on('show', function(ev){
    var $button = $(ev.target);
    var $display = $button.siblings('.datepicker-display');
    $button.datepicker('update', $display.text());
  })
  .on('changeDate', function(ev){
    var $button = $(ev.target);
    var $display = $button.siblings('.datepicker-display')
    var $hiddenInput = $button.siblings('.datepicker-hidden-input');
    $display.text(ev.format());
    $hiddenInput.val(ev.format());
  });
}).call(this);
