function [Prob, Cost, Util] = unwind(A)
    sites=columns(A)/3;

    % assume a tournament standard 24x80 field for now
    field_rows = 24;
    field_cols = 80;

    assert(sites, field_rows*field_cols);

    Prob = A(1:2:sites*2);
    Cost = A(2:2:sites*2);

    Util = A(:, sites*2+1:end);

    % reshape the arrays
    Prob = reshape(Prob, field_cols, field_rows)';
    Cost = reshape(Cost, field_cols, field_rows)';
    Util = reshape(Util, field_cols, field_rows)';
end
