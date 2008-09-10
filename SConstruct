import os.path

def protobuf_action(target,source,env,for_signature):
	"""
	Returns the action required to build the target from the source
	using the Google protocol buffer compiler.
	"""
	# target and source are lists of Node objects
	assert(len(target) == 1 and len(source) == 1)
	source_path = os.path.dirname(str(source[0]))
	target_path = os.path.dirname(str(target[0]))
	return 'protoc --python_out=%s --proto_path=%s %s' % (target_path,source_path,source[0])

# Add a custom builder for python protocol buffers
env = Environment()
env['BUILDERS']['ProtoBuf'] = Builder(generator=protobuf_action)

# Declare our protocol buffers
env.ProtoBuf('core/network/logging/logging_pb2.py','core/protobuf/logging.proto')
env.ProtoBuf('core/network/logging/archiving_pb2.py','core/protobuf/archiving.proto')