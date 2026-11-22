'use strict'; // #: Extend the existing builder without replacing its original digitiser or material inputs.
const materialPrototype=window.MagneticsBuilder.prototype, materialRender=materialPrototype.render; // #: Wrap the completed workflow/core renderer before application instantiation.
materialPrototype.render=function(){ // #: Add exchange controls only beside the ordinary material editor.
    materialRender.call(this); if(this.step!==2)return; // #: Preserve all existing handlers and other builder steps.
    const panel=document.createElement('section'); // #: Isolate additive material-point controls in their own subtree.
    panel.innerHTML='<h3>MAS material points</h3><p>Save permeability and reversible B–H points in SI with this complete design. Open restores its design for review before Use model. No catalogue, hysteresis, loss or temperature scaling is inferred. Nonlinear 3D remains unavailable.</p><button id="masMaterialSave">Save material exchange</button><button id="masMaterialOpen">Open material design</button><input id="masMaterialFile" type="file" accept=".json,application/json" hidden>'; // #: Explain point-only support and the complete-design replacement boundary.
    panel.querySelector('#masMaterialSave').onclick=async()=>{ // #: Export actual current builder inputs through the protected server.
        try{const packet=await this.api('/api/builder/mas-material-export',{specification:this.spec});this.save(JSON.stringify(packet,null,2),'MAS_Material_Points.json','application/json');this.message('Material points saved; temperature is a label, not a scaling law.');}catch(error){this.message(error.message,true);} // #: Preserve preview/workspace on rejected material or failed export.
    }; // #: Finish the explicit save handler.
    const input=panel.querySelector('#masMaterialFile'); // #: Use an independent chooser so original project/digitiser import remains unchanged.
    panel.querySelector('#masMaterialOpen').onclick=()=>{input.value='';input.click();}; // #: Permit reselecting a corrected copy of the same file.
    input.onchange=async event=>{ // #: Validate the complete retained design before installing a new preview.
        try{ // #: Keep the current builder and workspace on file/schema/material failures.
            const file=event.target.files[0];if(!file)return; // #: Cancelled selection leaves current inputs intact.
            if(file.size>2000000)throw Error('Material exchange must be below 2 MB'); // #: Bound decoding consistently with the HTTP body limit.
            const packet=JSON.parse(await file.text()); // #: Decode data only; never execute imported expressions.
            const result=await this.api('/api/builder/mas-material-apply',{packet,mode:this.spec.mode}); // #: Preserve the selected dimension and enforce actual nonlinear capability limits.
            if(!result.project?.builder||!result.summary)throw Error('Material import returned no checked builder design'); // #: Refuse an incomplete response before changing accepted inputs.
            this.spec=result.project.builder;this.latest=result;this.noRecipe=false;this.stale=false;this.render(); // #: Atomically install the checked design/preview; workspace fields stay untouched until Use model.
            this.message('Material design restored for review with its retained core, gaps, windings and layers. Use model to apply.'); // #: State that importing replaces the design from the packet rather than merging into unrelated fields.
        }catch(error){this.message(error.message,true);} // #: Expose actionable errors in the existing builder error panel.
    }; // #: Complete the bounded import handler.
    this.el.querySelector('.builder-form').append(panel); // #: Preserve all prior material/digitiser controls and attached events.
}; // #: Finish the additive pre-instantiation renderer wrapper.
