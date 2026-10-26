// Keep module-loading failures visible rather than leaving an empty workspace.
import('./app.js?v=2.5.13').catch(error=>{
 console.error('Loss Lab startup failed:',error);
 const root=document.querySelector('#page'),panel=document.createElement('section'),title=document.createElement('h1'),message=document.createElement('p'),detail=document.createElement('pre'),retry=document.createElement('button');
 panel.className='panel';title.textContent='The workspace could not start';message.textContent='Reload the page to try again. Saved studies in this browser have not been cleared.';detail.textContent=error?.message||String(error);retry.textContent='Reload workspace';retry.className='primary';retry.onclick=()=>location.reload();panel.append(title,message,detail,retry);root.replaceChildren(panel);
});
