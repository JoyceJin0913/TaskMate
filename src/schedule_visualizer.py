from flask import jsonify

@app.route('/api/events/<int:event_id>/completed', methods=['DELETE'])
def delete_completed_event(event_id):
    """删除已完成的事件"""
    try:
        success = timetable_processor.delete_completed_task(event_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '已完成事件已删除'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '删除已完成事件失败'
            }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'删除已完成事件时发生错误: {str(e)}'
        }), 500 