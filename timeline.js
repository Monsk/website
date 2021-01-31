jQuery(document).ready(function($){
var $timeline_block = $('.cd-timeline-block');

//hide timeline blocks which are outside the viewport
$timeline_block.each(function(){
if($(this).offset().top > $(window).scrollTop()+$(window).height()*0.75) {
$(this).find('.cd-timeline-marker, .cd-timeline-content-block').addClass('is-hidden');
}
});

//on scolling, show/animate timeline blocks when enter the viewport
$(window).on('scroll', function(){

$timeline_block.each(function(){
if( $(this).offset().top <= $(window).scrollTop()+$(window).height()*0.75 && $(this).find('.cd-timeline-content-block').hasClass('is-hidden') ) {
$(this).find('.cd-timeline-marker, .cd-timeline-content-block').removeClass('is-hidden').addClass('bounce-in');
}
});

// Scrolling progress bar
// var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
// var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
// var scrolled = (winScroll / height) * 100;
// document.getElementById("myBar").style.height = scrolled + "%";

});

});