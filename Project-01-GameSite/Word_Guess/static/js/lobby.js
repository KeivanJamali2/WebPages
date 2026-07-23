// Lobby enhancements: entrance cascade animation + subtle sound feedback
(function(){
	const cards = document.querySelectorAll('.room-card');
	if(!cards.length) return;
	// Cascade fade-in
	cards.forEach((c,i)=>{
		c.style.opacity='0';
		c.style.transform='translateY(18px) scale(.96)';
		setTimeout(()=>{
			c.style.transition='opacity .65s cubic-bezier(.25,.8,.25,1), transform .65s cubic-bezier(.25,.8,.25,1)';
			c.style.opacity='1';
			c.style.transform='translateY(0) scale(1)';
		}, 90*i);
		c.addEventListener('mouseenter', ()=>{ if(window.WGSounds) window.WGSounds.play('click',{playbackRate:1+Math.random()*.3}); });
	});
})();
