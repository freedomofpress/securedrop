# -*- coding: utf-8 -*-
from os.path import abspath, dirname, join

from alpaca import dists
from alpaca.morph_utils import create_object, morph_object
from alpaca.morphing import morph_page_distribution
from alpaca.sampling import KDEIndividual
from flask import render_template, Response

sampler = KDEIndividual(dists.counts, dists.html, dists.objects)

mimetype_switch = {
    'css': 'text/css',
    'js' : 'text/js',
    'png': 'image/png'
}

def render_morphed_template(template, **kwargs):
     original_html = render_template(template, **kwargs)
     morphed_html =  morph_page_distribution(original_html, sampler)
     return morphed_html.replace('/static/', '/morphed/')

def pad_static_resource(filename, type, size):
    abs_fname = join(abspath(dirname(__file__)), 'static', filename)
    content = open(abs_fname, 'rb').read()
    morphed_object = morph_object(content, type, size)
    return Response(morphed_object, mimetype=mimetype_switch[type])

def generate_random_object(size):
    random_object = create_object(size)
    return Response(random_object, mimetype='image/png')
