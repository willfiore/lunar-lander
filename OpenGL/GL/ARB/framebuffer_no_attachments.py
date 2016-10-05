'''OpenGL extension ARB.framebuffer_no_attachments

This module customises the behaviour of the 
OpenGL.raw.GL.ARB.framebuffer_no_attachments to provide a more 
Python-friendly API

Overview (from the spec)
	
	Framebuffer objects as introduced by ARB_framebuffer_object and OpenGL 3.0
	provide a generalized mechanism for rendering to off-screen surfaces.
	Each framebuffer object may have depth, stencil and zero or more color
	attachments that can be written to by the GL.  The size of the framebuffer
	(width, height, layer count, sample count) is derived from the attachments
	of that framebuffer.  In unextended OpenGL 4.2, it is not legal to render
	into a framebuffer object that has no attachments.  Such a framebuffer
	would be considered incomplete with the
	FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT status.
	
	With OpenGL 4.2 and ARB_shader_image_load_store, fragment shaders are
	capable of doing random access writes to buffer and texture memory via
	image loads, stores, and atomics.  This ability enables algorithms using
	the conventional rasterizer to generate a collection of fragments, where
	each fragment shader invocation will write its outputs to buffer or
	texture memory using image stores or atomics.  Such algorithms may have no
	need to write color or depth values to a conventional framebuffer.
	However, a framebuffer with no attachments will be considered incomplete
	and no rasterization or fragment shader exectuion will occur.  To avoid
	such errors, an application may be required to create an otherwise
	unnecessary "dummy" texture and attach it to the framebuffer (possibly
	with color writes masked off).  If the algorithm requires the rasterizer
	to operate over a large number of pixels, this dummy texture will
	needlessly consume a significant amount of memory.
	
	This extension enables the algorithms described above to work even with a
	framebuffer with no attachments.  Applications can specify default width,
	height, layer count, and sample count parameters for a framebuffer object.
	When a framebuffer with no attachments is bound, it will be considered
	complete as long as the application has specified non-zero default width
	and height parameters.  For the purposes of rasterization, the framebuffer
	will be considered to have a width, height, layer count, and sample count
	derived from its default parameters.  Framebuffers with one or more
	attachments are not affected by these default parameters; the size of the
	framebuffer will still be derived from the sizes of the attachments in
	that case.
	
	Additionally, this extension provides queryable implementation-dependent
	maximums for framebuffer width, height, layer count, and sample count,
	which may differ from similar limits on textures and renderbuffers.  These
	maximums will be used to error-check the default framebuffer parameters
	and also permit implementations to expose the ability to rasterize to an
	attachment-less framebuffer larger than the maximum supported texture
	size.

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/ARB/framebuffer_no_attachments.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.ARB.framebuffer_no_attachments import *
from OpenGL.raw.GL.ARB.framebuffer_no_attachments import _EXTENSION_NAME

def glInitFramebufferNoAttachmentsARB():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )

# INPUT glGetFramebufferParameteriv.params size not checked against 'pname'
glGetFramebufferParameteriv=wrapper.wrapper(glGetFramebufferParameteriv).setInputArraySize(
    'params', None
)
### END AUTOGENERATED SECTION