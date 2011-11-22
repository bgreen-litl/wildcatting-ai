function [] = plotfield(Field)
    colormap("default");

    h = imagesc(Field, [-1 1]);
    axis image off;
    drawnow;
end
