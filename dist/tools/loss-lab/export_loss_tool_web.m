function export_loss_tool_web(inputFile, outputFile)
% EXPORT_LOSS_TOOL_WEB Export a loss-tool snapshot/curve/table to portable JSON.
% Usage: export_loss_tool_web('snapshot.mat', 'web_project.json')
% Works around Legacy table/MCOS and v7.3 HDF5 browser import limitations.
% Original inputs and saved results are not modified. The web tool recomputes.
arguments
    inputFile (1,:) char
    outputFile (1,:) char
end
S = load(inputFile);
if isfield(S, 'state')
    out = struct('state', convertForWeb(S.state));
elseif isfield(S, 'curve')
    out = struct('curve', convertForWeb(S.curve));
else
    names = fieldnames(S);
    if numel(names) == 1 && istable(S.(names{1}))
        out = convertForWeb(S.(names{1}));
    else
        out = convertForWeb(S);
    end
end
text = jsonencode(out, 'PrettyPrint', true);
fid = fopen(outputFile, 'w', 'n', 'UTF-8');
if fid < 0, error('Cannot write output file: %s', outputFile); end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, '%s', text);
fprintf('Exported JSON to %s\n', outputFile);
end

function out = convertForWeb(v)
if istable(v)
    cols = struct();
    variables = v.Properties.VariableNames;
    for k = 1:numel(variables)
        x = v.(variables{k});
        if ~isnumeric(x) || ~isvector(x) || ~isreal(x)
            error('Waveform table variable %s must be a real numeric vector.', variables{k});
        end
        if any(~isfinite(x)), error('Waveform %s contains nonfinite values.', variables{k}); end
        cols.(variables{k}) = x(:).';
    end
    out = struct('columns', cols);
elseif isstruct(v)
    out = v;
    names = fieldnames(v);
    for j = 1:numel(v)
        for k = 1:numel(names)
            out(j).(names{k}) = convertForWeb(v(j).(names{k}));
        end
    end
elseif iscell(v)
    out = cell(size(v));
    for k = 1:numel(v), out{k} = convertForWeb(v{k}); end
elseif isnumeric(v) || islogical(v) || ischar(v) || isstring(v)
    if isnumeric(v) && ~isreal(v), error('Complex data is not supported.'); end
    out = v;
elseif isdatetime(v) || isduration(v)
    out = char(string(v));
else
    error('Unsupported snapshot value class: %s', class(v));
end
end
