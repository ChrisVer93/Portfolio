'use strict'; // #: Keep numerical chart generation deterministic and free of implicit assignments.
(function (root) { // #: Share the same dependency-free renderer with the application and verification tests.
    const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); // #: Escape all model labels and tooltip text before emitting SVG/HTML.
    const format = value => Number(value.toPrecision(5)).toString(); // #: Retain useful engineering precision without long binary tails.
    function chart(series, xLabel, yLabel, logX = false) { // #: Render signed physical values, optional log frequency and explicit missing-data gaps.
        const finite = point => point && Number.isFinite(point[0]) && Number.isFinite(point[1]) && (!logX || point[0] > 0); // #: Never convert null/undefined measurements to plotted zero values.
        const points = series.flatMap(s => s.points.filter(finite)); // #: Use actual finite samples to determine shared chart bounds.
        if (!points.length) return '<p class="hint">No defined values for this chart; zero-current V/I and lambda/I are undefined.</p>'; // #: Explain an empty measurement rather than manufacture a curve.
        const tx = value => logX ? Math.log10(value) : value; // #: Transform only the horizontal axis when frequency spans decades.
        const xs = points.map(p => tx(p[0])), ys = points.map(p => p[1]); // #: Keep the vertical axis signed and linear in the displayed engineering units.
        let xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys); // #: Fit all finite series including negative apparent inductances.
        if (xmin === xmax) {xmin -= .5; xmax += .5;} // #: A single defined point still needs a finite horizontal coordinate range.
        const pad = Math.max((ymax-ymin)*.1, Math.max(Math.abs(ymin),Math.abs(ymax))*.05, 1e-12); // #: Avoid visually exaggerating solver noise in a nominally constant inductance curve.
        ymin -= pad; ymax += pad; // #: Provide visible margins for constant, signed and zero-valued curves.
        const x = value => 76 + (tx(value)-xmin)/(xmax-xmin)*620; // #: Map physical horizontal values into the SVG plot rectangle.
        const y = value => 200 - (value-ymin)/(ymax-ymin)*140; // #: Map signed vertical values without clipping negative data.
        let svg = '<svg xmlns="http://www.w3.org/2000/svg" class="study-chart inductance-chart" viewBox="0 0 740 246" role="img" aria-label="'+escape(yLabel+' versus '+xLabel)+'"><title>'+escape(yLabel+' versus '+xLabel)+'</title>'; // #: Supply an accessible title, standalone SVG namespace and responsive intrinsic dimensions.
        svg += '<path d="M76 60V200H696" fill="none" stroke="#70869e"/>'; // #: Draw explicit plot axes independently of the sampled curves.
        for (let k=0;k<=4;k++) { // #: Give both axes readable numerical ticks.
            const fx=xmin+(xmax-xmin)*k/4, vy=ymin+(ymax-ymin)*k/4; // #: Use uniformly spaced displayed-coordinate tick positions.
            svg += '<text x="'+(76+620*k/4)+'" y="217" text-anchor="middle" fill="#b8c9dc" font-size="10">'+escape(format(logX?10**fx:fx))+'</text>'; // #: Invert log-axis coordinates back to hertz for tick labels.
            svg += '<text x="70" y="'+(204-140*k/4)+'" text-anchor="end" fill="#b8c9dc" font-size="10">'+escape(format(vy))+'</text>'; // #: Display the actual signed engineering scale on the vertical axis.
        } // #: End numerical axis tick generation.
        series.forEach((s,index) => { // #: Plot all explicitly labelled measurement definitions on the same axes.
            const colour=['#ffb36b','#82c9f4','#96d7ae','#d6a5f2'][index%4]; // #: Use a fixed trusted palette rather than model-supplied SVG attributes.
            const ordered=s.points.filter(p=>Array.isArray(p)&&Number.isFinite(p[0])).sort((a,b)=>a[0]-b[0]); // #: Order coordinate-bearing samples without mutating data or dereferencing a malformed point.
            let segment=[]; // #: Track a continuous run of defined measurements.
            const flush=()=>{if(segment.length>1)svg+='<polyline points="'+segment.join(' ')+'" fill="none" stroke="'+colour+'" stroke-width="2"/>';segment=[];}; // #: Break curves at undefined zero-current measurements instead of drawing through missing data.
            for (const point of ordered) { // #: Preserve each actual data point and its accessible physical tooltip.
                if (!finite(point)) {flush();continue;} // #: Missing or nonpositive log-frequency values terminate the current line segment.
                const px=x(point[0]),py=y(point[1]); // #: Map one verified finite point to chart coordinates.
                segment.push(px+','+py); // #: Extend only the current continuous line segment.
                svg+='<circle cx="'+px+'" cy="'+py+'" r="3.5" fill="'+colour+'"><title>'+escape(s.name+': '+format(point[0])+' '+xLabel+', '+format(point[1])+' '+yLabel)+'</title></circle>'; // #: Show real samples separately from connecting lines, with values on hover.
            } // #: End actual sample plotting.
            flush(); // #: Draw the last complete defined segment.
            svg+='<text x="76" y="'+(16+index*15)+'" fill="'+colour+'" font-size="11">'+escape(s.name)+'</text>'; // #: Identify each series and its definition with escaped legend text.
        }); // #: End independent series plotting.
        return svg+'<text x="386" y="240" text-anchor="middle" fill="#b8c9dc" font-size="11">'+escape(xLabel+(logX?' · log scale':''))+'</text><text x="696" y="49" text-anchor="end" fill="#b8c9dc" font-size="11">'+escape(yLabel)+'</text></svg>'; // #: Label physical axis units and close the self-contained SVG.
    } // #: Complete the pure chart renderer.
    const api={chart}; // #: Expose only the reusable renderer, not application state.
    root.MagneticsStudyCharts=api; // #: Make the same implementation available to the delivered browser scripts.
    if (typeof module!=='undefined' && module.exports) module.exports=api; // #: Permit direct Node verification without a browser or duplicated implementation.
})(typeof globalThis!=='undefined'?globalThis:window); // #: Bind to the current browser or test runtime explicitly.
