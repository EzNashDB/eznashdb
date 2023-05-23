(function setBodyHeight(){
    function resetBodyHeight(){
        document.body.style.height = window.innerHeight + "px";
    }
    window.addEventListener("resize", resetBodyHeight);
    resetBodyHeight();
})();

document.querySelectorAll('.tom-select').forEach((el)=>{
	let settings = {
        allowEmptyOption: true,
        maxItems: null,
        plugins: ["remove_button", "checkbox_options", "clear_button"],
    };
 	new TomSelect(el,settings);
});
