'use strict'; // #: Extend the existing builder without replacing its core/material/winding workflow.
const masCorePrototype = window.MagneticsBuilder.prototype, masCoreRender = masCorePrototype.render; // #: Wrap the final circuit-workflow builder before the application instantiates it.
masCorePrototype.render = function () { // #: Add explicit exchange controls in core dimension and gap steps.
    masCoreRender.call(this); // #: Preserve existing forms, preview, digitiser and winding handlers.
    if (![1,3].includes(this.step)) return; // #: Keep the new geometry-only controls beside the relevant inputs.
    const panel = document.createElement('section'); // #: Scope new controls and handlers to one additive subtree.
    panel.innerHTML = '<h3>MAS core geometry · symmetric rectangular EE</h3><p>Save editable SI E dimensions and explicit gaps with this full builder design. Open restores that design for review before Use model. Material names remain unresolved; no assembly-piece or curved-core geometry is inferred.</p><button id="masCoreSave">Save core exchange</button><button id="masCoreOpen">Open core design</button><input id="masCoreFile" type="file" accept=".json,application/json" hidden>'; // #: Explain exactly which source design will be restored and which upstream claims remain absent.
    panel.querySelector('#masCoreSave').onclick = async () => { // #: Export the actual current builder inputs through the protected server.
        try { // #: Surface unsupported geometry or fit failures in the existing builder error panel.
            const packet = await this.api('/api/builder/mas-core-export', {specification:this.spec}); // #: Validate original windings/material/core before producing the native geometry packet.
            this.save(JSON.stringify(packet,null,2), 'MAS_Core_Geometry.json', 'application/json'); // #: Download exact server-validated editable geometry and source metadata.
            this.message('Core exchange saved; SI dimensions and gap coordinates, not a complete MAS assembly.'); // #: Distinguish an actual export from a field solve or catalogue lookup.
        } catch (error) {this.message(error.message,true);} // #: Keep prior preview and workspace fields on export failure.
    }; // #: Complete the explicit export handler.
    const input = panel.querySelector('#masCoreFile'); // #: Use an independent chooser instead of changing existing project/recipe importers.
    panel.querySelector('#masCoreOpen').onclick = () => {input.value=''; input.click();}; // #: Permit selecting the same corrected file after a failed import.
    input.onchange = async event => { // #: Preview a complete retained builder design with deliberately edited native core data.
        try { // #: Validate file, JSON and core mapping before replacing builder inputs.
            const file = event.target.files[0]; if (!file) return; // #: A cancelled chooser leaves the current design alone.
            if (file.size>2000000) throw Error('Core exchange must be below 2 MB'); // #: Match the bounded server request size before decoding an oversized file.
            const packet = JSON.parse(await file.text()); // #: Do not execute imported expressions or accept a different file format silently.
            const result = await this.api('/api/builder/mas-core-apply', {packet,mode:this.spec.mode}); // #: Preserve the user's explicitly selected dimensional adapter and enforce current winding-fit constraints.
            if (!result.project?.builder || !result.summary) throw Error('Core import returned no checked builder design'); // #: Reject an incomplete response before replacing any accepted input or preview.
            this.spec=result.project.builder; this.latest=result; this.noRecipe=false; this.stale=false; this.render(); // #: Atomically install the already checked server design/preview without a second network request that could leave partially loaded state; workspace fields stay untouched.
            this.message('Core design restored for review; retained material, windings and layer order. Use model to replace workspace geometry.'); // #: Make the design replacement boundary explicit to the user.
        } catch (error) {this.message(error.message,true);} // #: Keep previous builder/workspace data after malformed, unsupported or stale geometry.
    }; // #: Complete the explicit file import/preview handler.
    this.el.querySelector('.builder-form').append(panel); // #: Preserve the original form elements and their attached events.
}; // #: Finish the additive builder extension.
