import os.path

def protobuf_action(target,source,env,for_signature):
	action = ('protoc --python_out=%s --proto_path=%s %s' %
		(os.path.dirname(target[0]),os.path.dirname(source[0]),os.path.basename(source[0]))
	)
	print '>>%s<<' % action
	return action

def test_action(target,source,env,for_signature):
	return 'echo %s %s' % (os.path.dirname(source[0]),target[0])

# protoc --python_out=design/archiving --proto_path=protobuf protobuf/archiving.proto

env = Environment()

env['BUILDERS']['ProtoBuf'] = Builder(generator=protobuf_action)

#env['BUILDERS']['TestMe'] = Builder(action = 'echo $TARGET $SOURCE')
env['BUILDERS']['TestMe'] = Builder(generator=test_action)

#env.ProtoBuf('core/network/logging/logging_pb2.py','core/protobuf/logging.proto')

env.TestMe('core/network/logging/logging_pb2.py','core/protobuf/logging.proto')