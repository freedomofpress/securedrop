var secure_drop = {
  init: function(){
    this.regenerate_ui();
  },
  regenerate_ui: function(){
    $('#regenerate-link').click(function(){
      $.ajax({
        url: '/gen_ajax/?words=10'
      }).done(function(resp){
        if(resp.result == "success"){
          $("#code-name").text(resp.id);
        } else {
          alert('Regenerate timed out.  Please try again.');
        }
      });
      return false;
    });
  }
};

$(function(){
  secure_drop.init();
});
