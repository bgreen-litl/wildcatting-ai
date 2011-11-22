function [] = plotfield(Field)
    colormap(gray);

    h = imagesc(Field, [-1 1]);
    axis image off;
    drawnow;
end
